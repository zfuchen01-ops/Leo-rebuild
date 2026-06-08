import sys
import copy
import pandas as pd
import numpy as np
import collections
np.random.seed(0)
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F

from Logger import Logger
from User import User
from Handover import Handover
from Topology import Topology
from Network import Network

log = Logger('./log/RL/DRQN.log',level='debug',w_level='info')


def resolve_device(device='auto'):
    if device == 'auto':
        return torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    return torch.device(device)

class UserReplayer:
    def __init__(self, capacity, sequence):
        self.capacity = capacity
        self.sequence = sequence
        self.memory = collections.deque(maxlen=self.capacity)

    def put(self, transition):
        self.memory.append(transition)

    def reset(self):
        self.memory.clear()

class CenterReplayer:
    def __init__(self, capacity, sequence):
        self.capacity = capacity
        self.sequence = sequence
        self.memory = {}

    def init_memory(self, agents):
        for agent in agents:
            self.memory[agent] = collections.deque(maxlen=self.capacity)

    def put(self, agent, transition):
        self.memory[agent].append(transition)
    
    def reset(self,agents):
        self.agents = agents
        self.memory.clear()
        self.init_memory(self.agents)
    
    def sample(self, size):
        states = []
        actions = []
        rewards = []
        next_states = []
        length = len(self.memory[self.agents[0]])-self.sequence+1


        indices = np.random.choice(len(self.agents)*length,size=size)
        for i in indices:
            agent_index = int(i/length)
            sample_index = int(i%length)
            temp_states = []
            temp_actions = []
            temp_rewards = []
            temp_next_states = []
            for j in range(self.sequence):
                temp_states.append(self.memory[self.agents[agent_index]][sample_index+j][0])
                temp_actions.append(self.memory[self.agents[agent_index]][sample_index+j][1])
                temp_rewards.append(self.memory[self.agents[agent_index]][sample_index+j][2])
                temp_next_states.append(self.memory[self.agents[agent_index]][sample_index+j][3])
            states.append(temp_states)
            actions.append(temp_actions)
            rewards.append(temp_rewards)
            next_states.append(temp_next_states)
        return states,actions,rewards,next_states

class Q_net(nn.Module):
    def __init__(self, state_space, action_space, hidden_size):
        super(Q_net, self).__init__()

        self.hidden_size = hidden_size
        self.input_size = state_space
        self.output_size = action_space

        self.lstm = nn.LSTM(self.input_size, self.hidden_size, batch_first=True)
        self.linear1 = nn.Linear(self.hidden_size, self.output_size)

    def forward(self, input, h, c):
        x, (new_h, new_c) = self.lstm(input,(h,c))
        y = self.linear1(x)
        return y, new_h, new_c

    def init_hidden_state(self, batch_size, train=None):
        if train is True:
            return torch.zeros([1, batch_size, self.hidden_size]), torch.zeros([1, batch_size, self.hidden_size])
        else:
            return torch.zeros([1, 1, self.hidden_size]), torch.zeros([1, 1, self.hidden_size])

class UserAgent:
    def __init__(self, user:User, env:Handover, c_agent, gamma=0.9, epsilon=0.01, batch=256, buffer=2000, hidden_size=64, seq=6, device='auto'):
        self.action_n = env.topo.total_sat
        self.gamma = gamma
        self.epsilon = epsilon
        self.batch_size = batch
        self.sequence = seq
        self.device = resolve_device(device)
        self.replayer = UserReplayer(buffer,self.sequence)

        self.evaluate_net = Q_net(3*self.action_n, self.action_n, hidden_size).to(self.device)

        self.user = user
        self.c_agent = c_agent
        self.env = env

    def reset(self, mode=None):
        self.mode = mode
        self.target_net = copy.deepcopy(self.evaluate_net).to(self.device)
        if self.mode == 'train':
            self.trajectory = collections.deque(maxlen=6)
            
    def step(self,observation,reward, h, c):
        if self.mode=='train' and np.random.rand()<self.epsilon:
            selected = []
            for sat in self.user.sat_covered:
                selected.append(sat.ID-1)
            action = np.random.choice(selected)
        else:
            state_tensor = torch.as_tensor(observation,dtype=torch.float).to(self.device).unsqueeze(0).unsqueeze(0)
            q_tensor, new_h, new_c = self.evaluate_net(state_tensor,h.to(self.device),c.to(self.device))
            q_tensor = q_tensor.squeeze(0).squeeze(0)
            for i in range(self.action_n):
                if observation[i]==-1.0:
                    q_tensor[i]=-1.0
                else:
                    q_tensor[i]+=100000.0   #修正q值，保证覆盖卫星的q值大于其他的，避免出错
            action_tensor = torch.argmax(q_tensor)
            action = action_tensor.item()
        if self.mode=='train':
            self.trajectory += [observation, reward, action]
            if len(self.trajectory)==6:
                state = self.trajectory[0]
                act = self.trajectory[2]
                next_state = self.trajectory[3]
                reward = self.trajectory[4]
                self.replayer.put([state,act,reward,next_state])
                self.c_agent.replayer.put(self,[state,act,reward,next_state])
        return action
    
    def observe(self,mode:str):
        observation = self.env.Observe(self.user,mode)
        return observation
    
    def get_reward(self):
        reward = self.env.Get_Reward(self.user)
        return reward
    

class CenterAgent:
    def __init__(self, env:Handover, gamma=0.9, epsilon=0.01, batch=256, buffer=20000, hidden_size=64, lr=0.001, seq=6, device='auto'):
        self.action_n = env.topo.total_sat
        self.gamma = gamma
        self.epsilon = epsilon
        self.batch_size = batch
        self.sequence = seq
        self.device = resolve_device(device)
        self.replayer = CenterReplayer(buffer,self.sequence)

        self.evaluate_net = Q_net(3*self.action_n, self.action_n, hidden_size).to(self.device)
        self.optimizer = optim.Adam(self.evaluate_net.parameters(), lr=lr)   #Adam包括偏置修正，修正从原点初始化的一阶矩（动量项）和（非中心的）二阶矩估计
        self.loss = nn.MSELoss()    #均方损失函数

        self.env = env

    def reset(self,agents):
        self.target_net = copy.deepcopy(self.evaluate_net).to(self.device)
        self.replayer.reset(agents)

    def learn(self):
        # replay
        states, actions, rewards, next_states = self.replayer.sample(self.batch_size) # replay transitions
        state_tensor = torch.as_tensor(states, dtype=torch.float).to(self.device)
        action_tensor = torch.as_tensor(actions, dtype=torch.long).to(self.device)
        reward_tensor = torch.as_tensor(rewards, dtype=torch.float).to(self.device)
        next_state_tensor = torch.as_tensor(next_states, dtype=torch.float).to(self.device)
        # train
        h_target, c_target = self.target_net.init_hidden_state(batch_size=self.batch_size, train=True)
        next_q_tensor, _, _= self.target_net(next_state_tensor,h_target.to(self.device), c_target.to(self.device))  #LSTM输出了tuple
        next_max_q_tensor, _ = next_q_tensor.max(axis=-1)
        target_tensor = reward_tensor + self.gamma * next_max_q_tensor

        h,c=self.evaluate_net.init_hidden_state(batch_size=self.batch_size, train=True)
        pred_tensor, _, _ = self.evaluate_net(state_tensor,h.to(self.device),c.to(self.device))
        q_tensor = pred_tensor.gather( 2, action_tensor.unsqueeze(2)).squeeze(2)
        loss_tensor = self.loss(target_tensor, q_tensor)
        self.optimizer.zero_grad()  #optimizer.zero_grad()意思是把梯度置零，也就是把loss关于weight的导数变成0.
        loss_tensor.backward()  #当完成计算后通过调用 .backward(),自动计算所有的梯度
        self.optimizer.step()
    
    def save_net(self, PATH):
        torch.save(self.evaluate_net, PATH)

def train_episode(env:Handover, u_agents, c_agent, model, mode=None,start_time=0, end_time=250000, time_step=50, net_step=20,batch=256):
    total_reward = 0.0  #训练阶段总回报
    reward_list = []
    time = start_time   #当前训练时刻
    episode = 0            #训练次数
    actions = {}        #每个时隙内的agent动作集
    env.reset(time,'NETWORK_LOAD')  #
    c_agent.reset(u_agents)
    temp_reward = 0     #用于计算某段时间内的平均
    ob_re = {}  #{agent:[observation,reward]}

    #用户agent初始化
    for agent in u_agents:
        agent.reset(mode=mode)
        ob_re[agent] = [agent.observe('NETWORK_LOAD'),0.0]
    while(time<=end_time):
        episode_reward = 0.0

        #终端进行action决策
        for agent in u_agents:
            ob_re[agent][0] = agent.observe('NETWORK_LOAD')
            h,c = agent.evaluate_net.init_hidden_state(batch,False)
            action = agent.step(ob_re[agent][0],ob_re[agent][1],h,c)
            actions[agent.user]= action+1
            episode_reward += ob_re[agent][1]
        total_reward += episode_reward
        temp_reward += episode_reward

        #replay达到一定容量，开始训练
        if len(u_agents[0].replayer.memory)>=0.5*u_agents[0].replayer.capacity:
            c_agent.learn()
            if(episode%net_step==0):
                c_agent.target_net = copy.deepcopy(c_agent.evaluate_net).to(c_agent.device)
            for agent in u_agents:
                agent.evaluate_net = copy.deepcopy(c_agent.evaluate_net).to(agent.device)
        
        #环境状态变更
        if episode==0:
            env.step(actions,'INITIAL')
        else:
            env.step(actions,'NETWORK')
        
        #数据记录
        log.logger.debug('time %d: reward = %.4f, episodes = %d',
            time, episode_reward, episode)
        if episode%400==399:
            average_reward = temp_reward/400.0
            log.logger.info('average_reward for past %d average_reward = %.4f, episodes = %d',
                400, average_reward, episode)
            #if average_reward>47:
                #break
            temp_reward = 0
        
        reward_list.append(episode_reward)
        time+=time_step
        episode+=1
        actions.clear()  
        for agent in u_agents:
            ob_re[agent][1] = agent.get_reward()
        env.Update_Env(time,'NETWORK_LOAD')
    log.logger.warning('from %d to %d by %d: average_reward = %.4f, episodes = %d',
        start_time, end_time, time_step, total_reward/episode, episode)
    c_agent.save_net('./log/model/%s.pkl'%model)
    env.close()
    reward_list[0] = -1
    reward_list[1] = -1
    return reward_list
