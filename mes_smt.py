import json
from httprequest import HttpRequest
class ExecMes:
    """
    K区
    mes_ip:10.58.10.113
    port:7014
    """
    def __init__(self,mes_ip:str,mes_port:str,sn:str,station_no:str,input_operNo:str="111"):

        self.mes_ip=mes_ip
        self.mes_port=mes_port
        self.sn=sn
        self.station_no=station_no
        self.input_operNo=input_operNo
        self.status_code=""
        self.text=""
        self.url=""
        self.params=""

    def check_station(self)->bool:
        

        self.status_code=""
        self.text=""
        """
        检测站点是否为当前站点
        """
        url = f"http://{self.mes_ip}:{self.mes_port}/test/v2/track"
        params = {
                "barCodes":[self.sn],
                "barCodeType": "SN",
                "terminalName": self.station_no,
                "eqpCode":f"",
                "ruleName":"TrackIn",
                "workOrder":f"",
                "operNo":self.input_operNo
            }
        ht=HttpRequest(url,json=params)
        ht.post()
        self.status_code=ht.status_code
        self.text=ht.text
        print(ht.status_code)
        print(ht.text)
        if ht.text["code"]==200 and ht.status_code==200:
            return (True,str(ht.text or ""))
        else:
            return (False,str(ht.text or ""))
 
    def get_info(self)->dict:
        """
        获取站点信息
        """
        self.status_code=""
        self.text=""
        url = f"http://{self.mes_ip}:{self.mes_port}/fs/test/getinfo"
        params = {
                "barCodes":[self.sn],
                "barCodeType": "SN",
                "terminalName": self.station_no,
                "eqpCode":f"",
                "workOrder":f"",
                "operNo":self.input_operNo
            }
        ht=HttpRequest(url,json=params)
        ht.post()
        self.status_code=ht.status_code
        self.text=ht.text
        print(ht.status_code )
        print(ht.text )
        if ht.text["code"]==200 and ht.status_code==200 and "data" in ht.text:
            mes_info=ht.text["data"][0]
            #data': [{'sn': 'SF43A5AG000101', 'mac': '772567882507B3'}]
            return mes_info
        else:
            return None
    def get_test_log(self):
        self.status_code=""
        self.text=""
        url = f"http://{self.mes_ip}:{self.mes_port}/fs/test/getinfo"   
        params = {
                "barCodes":[self.sn],
                "barCodeType": "SN",
                "terminalName": self.station_no,
                "eqpCode":f"",
                "workOrder":f"",
                "operNo":self.input_operNo
            }
        ht=HttpRequest(url,json=params)
        ht.post()
        self.status_code=ht.status_code
        self.text=ht.text
        print(ht.status_code )
        print(ht.text )
        if ht.text["code"]==200 and ht.status_code==200 and "data" in ht.text:
            mes_info=ht.text["data"][0]
            #data': [{'sn': 'SF43A5AG000101', 'mac': '772567882507B3'}]
            return mes_info
        else:
            return None
    def mes_outbound(self,result:str,error_msg:str,test_log="")->bool:#test_values:list[dict]=[]


        """
        站点出站
        result：PASS OR FAIL
        error code 最长30个字符
        """
        self.status_code=""
        self.text=""
        try:
            test_values=json.loads(test_log)
            # with open(r"D:\code\WPF_CODE\LuxAT\LuxAT\bin\x64\Debug\LuxLog\2026-11-06\out_smt.json", "w", encoding="utf-8") as f:
            #             json.dump(test_values, f, ensure_ascii=False, indent=2)   

        except:
            test_values=[]
            pass
        url = f"http://{self.mes_ip}:{self.mes_port}/test/v2/track"
        params = {
                "barCodes":[self.sn],
                "barCodeType": "SN",
                "terminalName": self.station_no,
                "eqpCode":f"",
                "ruleName":"TrackOut",
                "workOrder":"",
                "operNo":self.input_operNo,
                "collectData":{
                    "testInfo":[{"sn":self.sn,
                                "result":result,
                                "defectCode":error_msg,
                                "testValues":test_values
                                }]
                                }
            }
        print(url)
        print(params)
        # print(params)
        ht=HttpRequest(url,json=params)
        ht.post()
        self.status_code=ht.status_code
        self.text=ht.text
        print(ht.status_code )
        print(ht.text )
        try:
            if ht.status_code==200 :      #ht.text["code"]==200 and 
                return (True,str(ht.text or ""))
            else:
                return (False,str(ht.text or ""))
        except:
            return (False,str(ht.text))
    def test(self):
        return f"test: {self.mes_ip}, {self.mes_port}, {self.sn}, {self.station_no}, {self.input_operNo}"


if __name__=="__main__":
    mes_ip="10.58.10.113" #10.58.10.15
    # mes_ip="10.58.10.15" #10.58.10.15
    mes_port="7014"
    # mes_port="8990"
    station_no="FVI01"
    sn="6065-IPR1CA1-0000000C"
    exec_mes=ExecMes(mes_ip,mes_port,sn,station_no,"12786897")
    print(exec_mes.check_station())
    # print(exec_mes.get_info())
