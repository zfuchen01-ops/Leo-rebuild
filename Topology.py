from Constellation import Constellation
from Defination import *
from Position import Convert_PI_to_Angle,Calc_Sphere_Elevation
from User import User
from random import uniform
import os

def _log_path(path):
    return os.devnull if os.environ.get("LEO_QUIET_LOGS", "0") == "1" else path


Satout = open(_log_path("./log/topology/Sat_loc.log"), 'w')
Userout = open(_log_path("./log/topology/User_loc.log"), 'w')
Coverout = open(_log_path("./log/topology/Cover.log"), 'w')
class Topology:
    index_con = 0

    def __init__(self):
        self.total_sat = 0      
        self.total_user = 0
        self.current_time = 0   #当前拓扑时刻
        self.constellation = [] #星座
        self.user = []
        self.satellite = []

    #添加一整个星座
    def Add_Constellation(self, orbit_num, sat_num, height, first_phi, lean, theta, ctype):
        self.__class__.index_con += 1 #星座编号
        temp = Constellation()
        temp.Construct_Constellation(self.__class__.index_con,orbit_num,sat_num,height,first_phi,lean,theta,ctype)
        self.constellation.append(temp)
        self.total_sat += orbit_num*sat_num
        if os.environ.get("LEO_QUIET_LOGS", "0") != "1":
            print("Adding Constellation No.",self.__class__.index_con)
    
    def Each_Satellite(self):
        for con in self.constellation:
            for orbit in con.orbit_sat:
                for sat in orbit.sat_in_orbit:
                    self.satellite.append(sat)

    def Update_Topology_Status(self, time):
        self.Update_Sat_Coord(time)
        self.Update_Coverage()
        self.Record_Sat_Coord()
        self.Record_User_Coverage()

    #更新卫星坐标
    def Update_Sat_Coord(self, time):
        self.current_time = time
        for con in self.constellation:
            con.Get_Constellation_Condition(self.current_time)
    
    #更新当前时刻卫星与终端的可见性
    def Update_Coverage(self):
        for user in self.user:
            user.sat_covered.clear()
            for con in self.constellation:
                for orbit in con.orbit_sat:
                    for sat in orbit.sat_in_orbit:
                        elevation = Calc_Sphere_Elevation(sat.we_pos,user.we_pos)
                        if elevation>=USER_ELEVATION:
                            user.sat_covered.add(sat)

    def Record_Sat_Coord(self):
        if 1<=TOPO_LOG_LEVEL:
            return
        Satout.write("Time:%d\n"%self.current_time)
        for con in self.constellation:
            Satout.write("Constellation No.%d\n"%con.ID)
            Satout.write("%-6s%-10s%-10s%-10s\n"%('sid','longitude','latitude','height'))
            for orbit in con.orbit_sat:
                for sat in orbit.sat_in_orbit:
                    Satout.write("%-6d%-10.4f%-10.4f%-10d\n"%(sat.ID,Convert_PI_to_Angle(sat.we_pos.lon),
                                Convert_PI_to_Angle(sat.we_pos.lat),con.height))

    def Record_User_Coord(self):
        if 1<=TOPO_LOG_LEVEL:
            return
        Userout.write("Time:%d\n"%self.current_time)
        Userout.write("%-6s%-10s%-10s%-10s\n"%('uid','longitude','latitude','height'))
        for user in self.user:
            Satout.write("%-6d%-10.4f%-10.4f%-10d\n"%(user.ID,Convert_PI_to_Angle(user.we_pos.lon),
                        Convert_PI_to_Angle(user.we_pos.lat),user.height))

    def Record_User_Coverage(self):
        if 3<=TOPO_LOG_LEVEL:
            return
        Coverout.write("Time:%d\n"%self.current_time)
        Coverout.write("%-6s%s\n"%('uid','Sat_Covered'))
        for user in self.user:
            Coverout.write("%-6d"%user.user_ID)
            Coverout.write(','.join(str(x.ID) for x in user.sat_covered))
            Coverout.write('\n')
        #Coverout.flush()
    
    #更新当前时刻卫星与终端的可见性
    def Update_Coverage_Count(self):
        index = 0
        for user in self.user:
            user.sat_covered.clear()
            for con in self.constellation:
                for orbit in con.orbit_sat:
                    for sat in orbit.sat_in_orbit:
                        elevation = Calc_Sphere_Elevation(sat.we_pos,user.we_pos)
                        if elevation>=USER_ELEVATION:
                            user.sat_covered.add(sat)
            self.count[index] += len(user.sat_covered)
            index = index+1 

    def Init_Count(self):
        self.count = [0 for _ in range(len(self.user))]

    #指定位置添加一个终端
    def Add_User_Loc(self, lon, lat, height=USER_HEIGHT):
        temp = User(lon,lat,height)
        self.user.append(temp)
    
    #随机添加一个终端
    def Add_User(self):
        self.Add_User_Loc(uniform(-1*pi,pi),uniform(-0.35*pi,0.35*pi))

    #批量随机添加
    def Add_User_Batch(self, num):
        for i in range(num):
            self.Add_User()
    
    #按照位置数组批量添加
    def Add_User_From_Input(self, loc):
        for coord in loc:
            if(len(coord)!=2):
                print("Wrong location array")
                exit
            self.Add_User_Loc(coord[0],coord[1])
