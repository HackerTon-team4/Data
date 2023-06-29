from flask import Flask, send_file
import io
from bs4 import BeautifulSoup
import re
import requests as rq

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

# 데이터프레임을 CSV 파일로 저장하는 함수
def save_dataframe_as_csv(dataframe):
    buffer = io.StringIO()  # 문자열 버퍼 생성
    dataframe.to_csv(buffer, index=False)  # 데이터프레임을 CSV 형식으로 저장
    buffer.seek(0)  # 버퍼의 포인터를 처음으로 이동
    return buffer

@app.route('/')
def download_csv():
    # PER 수치를 기준으로 오름차순 정렬하여 상위 5개 종목 선택
    top_5_low_per = krx_ind.dropna(subset=['PER']).sort_values(by='PER').head(5)
    top_5_low_per = top_5_low_per[['종목코드', '종목명']]

    # 데이터프레임을 CSV 파일로 저장
    csv_buffer = save_dataframe_as_csv(top_5_low_per)

    # CSV 파일 다운로드
    return send_file(csv_buffer,
                     mimetype='text/csv',
                     as_attachment=True,
                     filename='top_5_low_per.csv')


if __name__ == '__main__':
    app.run()
