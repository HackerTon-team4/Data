from flask import Flask, render_template
import pandas as pd
import requests as rq
from bs4 import BeautifulSoup
import re
import requests as rq
import numpy as np

app = Flask(__name__)

url = 'https://finance.naver.com/sise/sise_deposit.nhn'
data = rq.get(url)
data_html = BeautifulSoup(data.content)
parse_day = data_html.select_one(
    'div.subtop_sise_graph2 > ul.subtop_chart_note > li > span.tah').text



biz_day = re.findall('[0-9]+', parse_day)
biz_day = ''.join(biz_day)

import requests as rq
from io import BytesIO
import pandas as pd

gen_otp_url = 'http://data.krx.co.kr/comm/fileDn/GenerateOTP/generate.cmd'
gen_otp_data = {
    'searchType': '1',
    'mktId': 'ALL',
    'trdDd': biz_day,
    'csvxls_isNo': 'false',
    'name': 'fileDown',
    'url': 'dbms/MDC/STAT/standard/MDCSTAT03501'
}
headers = {'Referer': 'http://data.krx.co.kr/contents/MDC/MDI/mdiLoader'}
otp = rq.post(gen_otp_url, gen_otp_data, headers=headers).text

down_url = 'http://data.krx.co.kr/comm/fileDn/download_csv/download.cmd'
krx_ind = rq.post(down_url, {'code': otp}, headers=headers)

krx_ind = pd.read_csv(BytesIO(krx_ind.content), encoding='EUC-KR')
krx_ind['종목명'] = krx_ind['종목명'].str.strip()
krx_ind['기준일'] = biz_day

# PER 수치를 기준으로 오름차순 정렬하여 상위 5개 종목 선택
top_5_low_per = krx_ind.dropna(subset=['PER']).sort_values(by='PER').head(5)

# 종목코드와 종목명으로 이루어진 데이터프레임 생성
top_5_low_per = top_5_low_per[['종목코드', '종목명']].reset_index(drop=True)

# 안정형을 위한 배당수익률 상위 5개 종목
top_5_high_allocation = krx_ind.sort_values(by='배당수익률', ascending=False).head(5)
top_5_high_allocation = top_5_high_allocation[['종목코드', '종목명']].reset_index(drop=True)

from datetime import datetime, timedelta

current_date = datetime.now().date()
year_ago_date = current_date - timedelta(days=730)
year_ago_date_str = year_ago_date.strftime('%Y%m%d')



# 1년 전 데이터 가져오기
gen_otp_url = 'http://data.krx.co.kr/comm/fileDn/GenerateOTP/generate.cmd'
gen_otp_data = {
    'searchType': '1',
    'mktId': 'ALL',
    'trdDd': year_ago_date_str,
    'csvxls_isNo': 'false',
    'name': 'fileDown',
    'url': 'dbms/MDC/STAT/standard/MDCSTAT03501'
}
headers = {'Referer': 'http://data.krx.co.kr/contents/MDC/MDI/mdiLoader'}
otp = rq.post(gen_otp_url, gen_otp_data, headers=headers).text

down_url = 'http://data.krx.co.kr/comm/fileDn/download_csv/download.cmd'
krx_ind_year_ago = rq.post(down_url, {'code': otp}, headers=headers)

krx_ind_year_ago = pd.read_csv(BytesIO(krx_ind_year_ago.content), encoding='EUC-KR')
krx_ind_year_ago['종목명'] = krx_ind_year_ago['종목명'].str.strip()
krx_ind_year_ago['기준일'] = year_ago_date_str

# 현재 데이터 가져오기
gen_otp_data['trdDd'] = biz_day
otp = rq.post(gen_otp_url, gen_otp_data, headers=headers).text

krx_ind = rq.post(down_url, {'code': otp}, headers=headers)
krx_ind = pd.read_csv(BytesIO(krx_ind.content), encoding='EUC-KR')
krx_ind['종목명'] = krx_ind['종목명'].str.strip()
krx_ind['기준일'] = biz_day

# EPS 성장률 계산
eps_growth_rate = ((krx_ind['EPS'] - krx_ind_year_ago['EPS']) / krx_ind_year_ago['EPS']) * 100
krx_ind['EPS 성장률'] = eps_growth_rate.where(eps_growth_rate.notnull(), np.nan)

peg = krx_ind['PER'] / krx_ind['EPS 성장률']
krx_ind['PEG'] = peg.where(peg.notnull(), np.nan)

## 공격형을 위한 PEG 상위종목 5개
top_5_low_peg = krx_ind.dropna(subset=['PEG']).sort_values(by='PEG').head(5)
top_5_low_peg = top_5_low_peg[['종목코드', '종목명']].reset_index(drop=True)

@app.route('/')
def index():
    # 데이터프레임을 HTML 템플릿에 전달하여 표시
    table1 = top_5_low_per.to_html(index=False)
    table2 = top_5_high_allocation.to_html(index=False)
    table3 = top_5_low_peg.to_html(index=False)

    # 템플릿 파일에 데이터 전달하여 렌더링
    return render_template('index.html', table1=table1, table2=table2, table3=table3)


if __name__ == '__main__':
    app.run()
