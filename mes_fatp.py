import json
from httprequest import HttpRequest
class ExecMes:
    """
    G区
    mes_ip:10.33.20.134
    port:8033

    """
    def __init__(self,mes_ip:str,mes_port:str,sn:str,station_no:str,operNo="123"):
        self.mes_ip=mes_ip
        self.mes_port=mes_port
        self.sn=sn
        self.station_no=station_no
        self.status_code=None
        self.text=None

    def check_station(self)->bool:
        """
        检测站点是否为当前站点
        
        """
        self.text=""
        url = f"http://{self.mes_ip}:{self.mes_port}/api/3/CHKRoute/serial/{self.sn}/station/{self.station_no}"
        hp=HttpRequest(url)
        hp.post()
        self.status_code=hp.status_code
        self.text=hp.text
        # print(f"MESINFO:{repr(hp.status_code)}")
        # print(f"MESINFO:{repr(hp.text)}")
        if hp.status_code==200 and hp.text["code"]==200:
            return (True,self.text)
        else:
            return (False,self.text)
    def get_info_beacon(self)->dict:
        """
        获取MES信息 fs/test/getinfo
        """
        url=f"http://{self.mes_ip}:{self.mes_port}/api/FS01/CheckRouteAndGetMac/serial/{sn}/station/{station_no}" 
        # url=f"http://{self.mes_ip}:{self.mes_port}/fs/test/getinfo" 
        # params = {
        #     "barCodes": [self.sn],
        #     "barCodeType": "SN",
        #     "terminalName": self.station_no,
        #     "eqpCode":"",
        #     "workOrder":"TEST_MAC",
        #     "operNo":"12898402"
        # }
        
        ht=HttpRequest(url)
        ht.post()
        self.status_code=ht.status_code
        self.text=ht.text
        print(f"MESINFO:{repr(ht.status_code)}")
        print(f"MESINFO:{repr(ht.text)}")
        if ht.text["code"]==200 and ht.status_code==200 and "data" in ht.text:
            mes_info=ht.text["data"][0]
            # print(f"mes_info: {mes_info}",flush=True)
            return mes_info
            #data': [{'sn': 'SF43A5AG000101', 'mac': '772567882507B3'}]
        else:
            return None
    def get_info_testLog(self)->dict:
        """
        获取MES信息 BB验证ok 之前上传 mes_outbound 上传内容 检查站点
        """
        #url=f"http://{mes_ip}:{mes_port}/api/FS01/CheckRouteAndGetMac/serial/{sn}/station/{station_no}" 
        #http://IP:port/api/api/3/CheckRouteAndGetTestDate/serial/{serial}/station/{station}/processname
        #http://IP:port/api/api/3/CheckRouteAndGetTestDate/serial/{serial}/station/{station}/processname/{processname?}
        url=f"http://{self.mes_ip}:{self.mes_port}/api/3/CheckRouteAndGetKPSN/serial/{self.sn}/station/{self.station_no}/processname" 
 
 
        ht=HttpRequest(url)
        ht.post()
        self.status_code=ht.status_code
        self.text=ht.text
        print(f"MESINFO:{repr(ht.status_code)}")
        print(f"MESINFO:{repr(ht.text)}")
        if ht.text["code"]==200 and ht.status_code==200 and "data" in ht.text:
            mes_info=ht.text["data"][0]
            # print(f"mes_info: {mes_info}",flush=True)
            return mes_info
         
        else:
            return None
    def get_info_tmp(self):
        url=f"http://{self.mes_ip}:{self.mes_port}/api/3/CHKRouteOutKBDSNMAC/serial/{self.sn}" 
        ht=HttpRequest(url)
        ht.post()
        self.status_code=ht.status_code
        self.text=ht.text
        print(f"MESINFO:{repr(ht.status_code)}")
        print(f"MESINFO:{repr(ht.text)}")
        if ht.text["code"]==200 and ht.status_code==200 and "data" in ht.text:
            mes_info=ht.text["data"][0]
            # print(f"mes_info: {mes_info}",flush=True)
            return mes_info
            #data': [{'sn': 'SF43A5AG000101', 'mac': '772567882507B3'}]
        else:
            return None

    def mes_outbound(self,result:str,error_msg:str,test_log="")->bool:#testdata:dict={}
        
        """
        站点出站
        error code 最长30个字符
        """
        self.text=""
        try:
            testdata = json.loads(test_log)      # dict
        except:
            testdata=None
            pass
        # with open(r"D:\code\WPF_CODE\LuxAT\LuxAT\bin\x64\Debug\LuxLog\2026-11-06\out.json", "w", encoding="utf-8") as f:
        #     json.dump(ress, f, ensure_ascii=False, indent=2)

        url = f"http://{self.mes_ip}:{self.mes_port}/api/3/serial/{self.sn}/station/{self.station_no}/info"
        params = {
            "serial": self.sn,
            "start_time": "",
            "finish_time": "",
            "status":result,
            "error_code":error_msg,
            "Fix_Num":self.station_no,
        }
        if testdata:
            params.update(testdata)
        hp=HttpRequest(url,params=params)
        hp.post()
        self.status_code=hp.status_code
        self.text=hp.text
        print(f"mes status code: {hp.status_code}" )
        # data = json.loads(hp.text)
        print(f"mes response: {hp.text}" )
        if hp.status_code==200 : #and hp.text["code"]==200
            return (True,self.text)
        else:
            return (False,self.text)



if __name__=="__main__":
    # mes_ip="10.33.20.134" #10.58.10.15   G 
    # mes_port="8033"
    mes_ip="10.58.10.15" #10.58.10.15
    mes_ip="10.58.10.113" #K
    mes_ip="10.33.20.134" #G d
    mes_port="8990"
    mes_port="7014" #K
    mes_port="8033" #g d
    station_no="cosmetic inspection01"
    sn="FS01BL620000041"
    exec_mes=ExecMes(mes_ip,mes_port,sn,station_no)
    print(exec_mes.check_station())
    print(exec_mes.get_info_beacon())
    
