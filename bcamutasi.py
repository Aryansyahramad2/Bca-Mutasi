import json
import pandas as pd
from datetime import datetime
from os import environ
from pytz import timezone
from requests import Session,get
from dotenv import load_dotenv
from bs4 import BeautifulSoup as bs

load_dotenv()

ENDPOINT = 'https://ibank.klikbca.com'
PATH_LOGIN = '/authentication.do'
PATH_SALDO = '/balanceinquiry.do'
PATH_HISTORY = '/history.do'
PATH_MUTASI_VIEW = '/accountstmt.do?value(actions)=acctstmtview'
PATH_MUTASI_DONWLOAD = '/accountstmt.do?value(actions)=acctstmtview'


BCAUSER = environ.get('BCAUSER','USER123456')
BCAPIN = environ.get('BCAPIN','123456')
WEBWOOK = environ.get('WEBWOOK',None)

MY_IP = get('https://api.ipify.org/').text




class BCAMutasi:
    def __init__(self) -> None:
        self._session = Session()
        self._session.verify = False
        self._login = False
    
    def login(self):
        data ={
            'value(actions)':'login',
            'value(user_id)':BCAUSER,
            'value(user_ip)':MY_IP,
            'value(pswd)':BCAPIN,
            'value(Submit)':'LOGIN',
        }
        res = self._session.post(ENDPOINT+PATH_LOGIN,data)
        html = bs(res.text,'html.parser')
        success = html.find_all('input',{'name':'value(pswd)'})
        if res.status_code == 200 and len(success) == 0:
            self._login = True
        
    def history_today(self):
        data ={
            'value(actions)': 'historylist',
            'value(periode)': '0',
            'value(txntype)': '0',
            'value(jnstxn)': 'Transfer to BCA Account',
            'value(submit)': 'Submit',
        }

    def donwload_csv(self):
        if not self._login:
            return
        data = self.get_payload
        data.update({
            "value(fDt)":"", 
            "value(tDt)":"", 
            "value(submit2)":"Statement Download" })

        res = self._session.post(ENDPOINT+PATH_MUTASI_DONWLOAD,data)
        dfs = pd.read_html(res.text)
        df1 = dfs[3].copy()
        df2 = dfs[4].copy()
        df3 = dfs[5].copy()
        if len(df2.columns) !=6:
            return
        df2.columns = ['date','ket','branch','nom','type','sal']
        df2 = df2[1:]
        df2[['nom','sal']] = df2[['nom','sal']].astype(float)
        today = datetime.now(timezone('Asia/Jakarta'))
        df2['date'] = datetime(today.year,today.month,today.day)
        data = json.loads(df2.to_json(orient='records')) 
        return data

    @property
    def get_payload(self)->dict:
        today = datetime.now(timezone('Asia/Jakarta'))
        data = {
            'value(r1)':'1',
            'value(startDt)':str(today.day),
            'value(startMt)':str(today.month),
            'value(startYr)':str(today.year),
            'value(endDt)':str(today.day),
            'value(endMt)':str(today.month),
            'value(endYr)':str(today.year),
            'value(D1)':'0',
        }
        return data

    def logout(self):
        data = {'value(actions)':'logout'}
        res=self._session.post(ENDPOINT+PATH_LOGIN,data)
        html = bs(res.text,'html.parser')
        success = html.find_all('input',{'name':'value(pswd)'})
        if res.status_code == 200 and len(success) != 0:
            self._login = False

    def call_webhook(self,data):
        if WEBWOOK == None:
            print(data)
            return
        self._session.post(WEBWOOK,json=data)

def main():
    coba = BCAMutasi()
    coba.login()
    coba.donwload_csv()
    coba.logout()


if __name__ == '__main__':
    main()