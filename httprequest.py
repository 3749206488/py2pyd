import requests

class HttpRequest:
    def __init__(self, url, params=None,json=None):
        self.url = url
        self.params = params
        self.json = json
        self.response = None
        self.status_code = None
        self.text = None
 
    def post(self):
        try:
            self.response = requests.post(self.url, data=self.params,json=self.json)
            self.status_code = self.response.status_code
            self.text = self.response.json()
        except Exception as e:
            print(f"error: {e}")
            self.text = f"error: {e}"
    def get(self):
        try:
            self.response = requests.get(self.url, params=self.params,json=self.json)
            self.status_code = self.response.status_code
            self.text = self.response.json()
        except requests.exceptions.RequestException as e:
            print(f"error: {e}")
            self.text = f"error: {e}"
    def put(self):
        try:
            self.response = requests.put(self.url, data=self.params,json=self.json)

            self.status_code = self.response.status_code
            self.text = self.response.json()
        except requests.exceptions.RequestException as e:
            print(f"error: {e}")
            self.text = f"error: {e}"

    def patch(self):
        try:
            self.response = requests.patch(self.url, data=self.params)
            self.status_code = self.response.status_code
            self.text = self.response.json()

        except requests.exceptions.RequestException as e:
            print(f"error: {e}")
            self.text = f"error: {e}"
    def head(self):
        try:
            self.response = requests.head(self.url, data=self.params)
            self.status_code = self.response.status_code
            self.text = self.response.json()
        except requests.exceptions.RequestException as e:
            print(f"error: {e}")
            self.text = f"error: {e}"

if __name__ == "__main__":

    # url = "http://10.32.13.198/bobcat/sfc_response.aspx" # C区
    url = 'http://10.58.10.15:8990/api/KibeamPVTKB01/CheckIsRoute' #验证用服务器
    '''
    检查是否为当前站点    http://10.33.20.134:8033/api/KibeamPVTKB01/CheckIsRoute  
       params = {
            "SERIALNUMBER": "TESTJT12352",
            "TERMINAL_Name":"KIB01_lens quick check01",
           } 
    过站
    http://10.33.20.134:8033/api/KibeamPVTKB01/CheckSNPass
     params =  { 
    "SERIALNUMBER": "TESTJT12345", 
    "TERMINAL_Name":"KIB01_lens quick check01",  
    "TestCode":"OK" pass-->OK return info:ok  fail-->NG
    }

    过站含测试信息
    http://10.58.10.15:8990/api/2/serial/TESTJT12345/station/KIB01_Focus test01/info
    params =  { 
    "serial": "TESTJT12345", 
    "start_time": "2025-04-01 00:30:11", 
    "finish_time": "2025-04-01 00:33:22", 
    "status": "passed",   ng-->fail
    "error_code": "", 
    "Fix_Num": "KIB01_Focus test01", 
    "test_time": "191.2062423"

    }

    '''
     
   
    # url = "http://10.33.20.134:8033/api/Nokia/getCodeinfo/serial/FS01BL5B0000014" # k区
    # params = {
    #     "c": "QUERY_RECORD",
    #     "sn": "W003202511000562", 
    #     "p": "unit_process_check",
    #     "tsid": "WO03_Print_RSN_Label01"
    # }
    # params = {
       
    #         "SERIALNUMBER": "TESTJT12352",
    #         "TERMINAL_Name":"KIB01_lens quick check01",
    # }
    # hr=HttpRequest(url,json=params)
    # hr.post()
    # print(hr.status_code)
    # print(F"结果 {hr.text}")
    # print(hr.text["Mnemonic"])
  


    #new 
    mes_ip="10.58.10.113"
    mes_port="7014"
    sn="5425IPR1BA100000004"
    station_no="K2-3F-S02-B-P01"
    index=1
    # input_operNo="1"
    input_operNo="12898402"
    workorder="TEST_MAC"

    sn="FS01BL5B0000027"
    mes_ip="10.33.20.134"
    mes_port="8033"
    station_no="Function test01"
    # workorder="TEST_MAC"
    # ====================================================================
    # 检测站点是否为当前站点
    # print(f"检测站点是否为当前站点 {sn} {station_no} {index} {input_operNo}  ")

    # url = f"http://{mes_ip}:{mes_port}/test/v2/track"
    # params = {
    #                 "barCodes":[sn],
    #                 "barCodeType": "SN",
    #                 "terminalName": station_no,
    #                 "eqpCode":f"window_{index}",
    #                 "ruleName":"TrackIn",
    #                 "workOrder":f"",
    #                 "operNo":input_operNo
    #             }
    #"TERMINAL_Name":"CX_link KBD01"

    url = f"http://{mes_ip}:{mes_port}/api/CHKRoute/serial/{sn}/station/{station_no}"
    hr=HttpRequest(url)

    hr.post()
    print(hr.status_code)
    print(F"结果 {hr.text}")
    print(hr.text["code"])
    print(hr.text["message"])

    # 获取信息
    print(f"获取信息 {sn} {station_no} {index} {input_operNo}  ")

    url = f"http://{mes_ip}:{mes_port}/fs/test/getinfo"
    params = {
                    "barCodes":[sn],
                    "barCodeType": "SN",
                    "terminalName": station_no,
                    "eqpCode":f"",
                    "workOrder":f"",
                    "operNo":input_operNo
                }
    hr=HttpRequest(url,json=params)
    hr.post()
    print(hr.status_code)
    print(F"结果 {hr.text}")
    print(hr.text["code"])
 
    print(hr.text["data"][0]["sn"])
    print(hr.text["data"][0]["mac"])


    # 过站
    # error_msg="TEST_ERROR"
    # print(f"过站 {sn} {station_no} {index} {input_operNo} {error_msg}")


    # url = f"http://{mes_ip}:{mes_port}/test/v2/track"
    # params = {
    #                 "barCodes":[sn],
    #                 "barCodeType": "SN",
    #                 "terminalName": station_no,
    #                 "eqpCode":f"window_{index}",
    #                 "ruleName":"TrackOut",
    #                 "workOrder":"",
    #                 "operNo":input_operNo,
    #                 "collectData":{
    #                     "testInfo":[{"sn":sn,
    #                                  "result":"PASS",
    #                                  "defectCode":"",
    #                                  "testValues":[
    #                                      {"key":"TEST_SN","value":sn},
    #                                      {"key":"TEST_RESULT","value":"PASS"}
    #                                      ]
    #                                  }]
    #                                 }
    #             }
    # hr=HttpRequest(url,json=params)
    # hr.post()
    # print(hr.status_code)
    # print(F"结果 {hr.text}")




'''
Ok:

{"code":200,"info":"OK","data":null}

检查站点：
    oK:{"code":200,"info":"OK","data":null}

    NG:{"code":400,"info":"Next:KIB01_lens quick check /Current:KIB01_Focus t","data":null}

error:
{"code":500,"info":"未收到测试结果，请测试后上传","data":null}

'''