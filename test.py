import requests  # 보내고자 하는 ip로 전송하기 위해 라이브러리
import json  # python data 형식을 json 형식으로 변환하기 위한 라이브러리
from bs4 import BeautifulSoup
import re
import requests as rq
import numpy as np
from flask import Flask, jsonify, request
import logging

app = Flask(__name__)

# URL(Public IP)
url = "http://52.79.214.212:8080"  # 해당 IP는 설명하기 위한 IP이지, 작성자가 사용하는 IP가 아님.

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

######## 가치투자형을 위한 PER 상위 5개 종목 #########
top_5_low_per = top_5_low_per[['종목코드', '종목명']].reset_index(drop=True)
top_5_low_per.columns = ['stockCode', 'name']

######### 안전형을 위한 배당수익률 상위 5개 종목 ##########
top_5_high_allocation = krx_ind.sort_values(by='배당수익률', ascending=False).head(5)
top_5_high_allocation = top_5_high_allocation[['종목코드', '종목명']].reset_index(drop=True)
top_5_high_allocation.columns = ['stockCode', 'name']

####### 수익형을 위한 BPS 상위 5개 종목 #########
top_5_high_BPS = krx_ind.sort_values(by='BPS', ascending=False).head(5)
top_5_high_BPS = top_5_high_BPS[['종목코드', '종목명']].reset_index(drop=True)
top_5_high_BPS.columns = ['stockCode', 'name']

from datetime import datetime, timedelta

current_date = datetime.now().date()
year_ago_date = current_date - timedelta(days=730)
year_ago_date_str = year_ago_date.strftime('%Y%m%d')

# 2년 전 데이터 가져오기
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

###### 공격형을 위한 PEG 상위종목 5개 #######
top_5_low_peg = krx_ind.dropna(subset=['PEG']).sort_values(by='PEG').head(5)
top_5_low_peg = top_5_low_peg[['종목코드', '종목명']].reset_index(drop=True)
top_5_low_peg.columns = ['stockCode', 'name']


@app.route('/api/dataframe', methods=['POST'])
def get_dataframe():
    logging.info('get_dataframe')
    answers = request.get_json()
    logging.info(answers)
    arr1 = [k["answer"] for k in answers]

    for QandA in answers:
        logging.info(QandA)

    result1, result2 = CAVB(arr1)
    recommended_stocks = []

    if result1[0] == 'C':
        recommended_stocks = top_5_high_allocation.to_dict('records')
    elif result1[1] == 'A':
        recommended_stocks = top_5_low_peg.to_dict('records')
    elif result1[2] == 'V':
        recommended_stocks = top_5_low_per.to_dict('records')
    elif result1[3] == 'B':
        recommended_stocks = top_5_high_BPS.to_dict('records')

    recommended_data = {
        "mbti": result1,
        "Jbti": result2,
        "stocks": recommended_stocks
    }

    return jsonify(recommended_data)


def CAVB(arr):
    c = 0  # 안전
    a = 0  # 공격
    v = 0  # 가치
    b = 0  # 수익

    E = 0
    I = 0
    S = 0
    N = 0
    T = 0
    F = 0
    P = 0
    J = 0

    if arr[0] == 1:
        E += 1
    else:
        I += 1

    if arr[1] == 1:
        N += 1
    else:
        S += 1

    if arr[2] == 1:
        T += 1
    else:
        F += 1

    if arr[3] == 1:
        P += 1
    else:
        J += 1

    if arr[4] == 1:
        c = c + 0
    else:
        c += 1

    if arr[5] == 1:
        c += 1
    else:
        a += 1

    if arr[6] == 1:
        c += 1
    else:
        a += 1
        b += 1

    if arr[7] == 1:
        c += 1
    else:
        c = c + 0

    if arr[8] == 1:
        c += 1
    else:
        a += 1
        b += 1

    if arr[9] == 1:
        c = c + 0
    else:
        c += 1

    if arr[10] == 1:
        a += 1
    else:
        c += 1
    if arr[11] == 1:
        a += 1
    else:
        a += 0
    if arr[12] == 1:
        a += 1
    else:
        a += 0
    if arr[13] == 1:
        a += 0
    else:
        a += 1
    if arr[14] == 1:
        c += 1
    else:
        a += 1
    if arr[15] == 1:
        b += 1
    else:
        v += 1
    if arr[16] == 1:
        b += 1
    else:
        v += 1
    if arr[17] == 1:
        b += 1
        a += 1
    else:
        v += 1
        c += 1
    if arr[18] == 1:
        v += 1
    else:
        b += 1
    if arr[19] == 1:
        v += 1
    else:
        b += 1
        v += 1
    if arr[20] == 1:
        v += 1
    else:
        b += 1
    if arr[21] == 1:
        v += 1
    else:
        v += 0
    if arr[22] == 1:
        v += 1
    else:
        v += 0
    if arr[23] == 1:
        v += 1
    else:
        v += 0
        b += 1

    if E == 1:
        str_mbti = 'E'
    if I == 1:
        str_mbti = 'I'
    if S == 1:
        str_mbti = str_mbti + 'S'
    if N == 1:
        str_mbti = str_mbti + 'N'
    if T == 1:
        str_mbti = str_mbti + 'T'
    if F == 1:
        str_mbti = str_mbti + 'F'
    if J == 1:
        str_mbti = str_mbti + 'J'
    if P == 1:
        str_mbti = str_mbti + 'P'

    if c > 5:
        str_cavb = 'C'
    else:
        str_cavb = 'c'

    if a > 5:
        str_cavb = str_cavb + 'A'
    else:
        str_cavb = str_cavb + 'a'

    if v > 5:
        str_cavb = str_cavb + 'V'
    else:
        str_cavb = str_cavb + 'v'

    if b > 5:
        str_cavb = str_cavb + 'B'
    else:
        str_cavb = str_cavb + 'b'

    return str_cavb, str_mbti


if __name__ == '__main__':
    app.run(host='0.0.0.0')