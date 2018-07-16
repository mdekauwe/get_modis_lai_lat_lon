#!/usr/bin/env python

"""
Get MODIS LAI for a lat,lon point or area around a point.

To do:
- get lai_sd
- screen by good QA
- add the other old missing functionality

That's all folks.
"""

__author__ = "Martin De Kauwe"
__version__ = "1.0 (17.07.2018)"
__email__ = "mdekauwe@gmail.com"

import requests
import json
import datetime
import pandas as pd
import numpy as np
import sys


def main(url, header, lat, lon, prod, band, sd_band, qc_band, above_below,
         left_right, start_year, end_year):

    dates = build_date_list(start_year, end_year)

    #******* TESTING REMOVE **********#
    dates = dates[0:25]

    lai_data = []
    sd_data = []
    qc_data = []

    # loop in increments of 10 so we don't crash the server
    for dt in range(0, len(dates) - 10, 10):

        # Build LAI request url and submit request
        request_url = build_request(url, prod, lat, lon, band, dates, dt,
                                    dt+9, above_below, left_right)
        response = requests.get(request_url, headers=header)

        # Loop through list of dictionaries inside the subset key of the
        # response and append data to lai_data
        scale = float(json.loads(response.text)['scale'])
        for tstep in json.loads(response.text)['subset']:
            vals = tstep['data']
            vals = [i*scale for i in vals]
            lai_data.append(vals)

        # Build LAI SD request url and submit request
        request_url = build_request(url, prod, lat, lon, sd_band, dates, dt,
                                    dt+9, above_below, left_right)
        response = requests.get(request_url, headers=header)

        # Loop through list of dictionaries inside the subset key of the
        # response and append data to lai_data
        scale = float(json.loads(response.text)['scale'])
        for tstep in json.loads(response.text)['subset']:
            vals = tstep['data']
            vals = [i*scale for i in vals]
            sd_data.append(vals)

        # Build QC request url and submit request
        request_url = build_request(url, prod, lat, lon, qc_band, dates, dt,
                                    dt+9, above_below, left_right)
        response = requests.get(request_url, headers=header)

        # Loop through list of dictionaries inside the subset key of the
        # response and append data to qc_data
        for tstep in json.loads(response.text)['subset']:
            qc_data.append(tstep['data'])

    # We may still have dates left over. Submit requests for the last <=10
    # dates.

    # Build LAI request url and submit request
    request_url = build_request(url, prod, lat, lon, band, dates, dt+10,
                                -1, above_below, left_right)
    response = requests.get(request_url, headers=header)

    # Loop through list of dictionaries inside the subset key of the response
    # and append data to lai_data
    scale = float(json.loads(response.text)['scale'])
    for tstep in json.loads(response.text)['subset']:
        vals = tstep['data']
        vals = [i*scale for i in vals]
        lai_data.append(vals)

    # Build LAI request url and submit request
    request_url = build_request(url, prod, lat, lon, sd_band, dates, dt+10,
                                -1, above_below, left_right)
    response = requests.get(request_url, headers=header)

    # Loop through list of dictionaries inside the subset key of the response
    # and append data to lai_data
    scale = float(json.loads(response.text)['scale'])
    for tstep in json.loads(response.text)['subset']:
        vals = tstep['data']
        vals = [i*scale for i in vals]
        sd_data.append(vals)

    # Build QC request url and submit request
    request_url = build_request(url, prod, lat, lon, qc_band, dates, dt+10,
                                -1, above_below, left_right)
    response = requests.get(request_url, headers=header)

    # Loop through list of dictionaries inside the subset key of the response
    # and append data to qc_data
    for tstep in json.loads(response.text)['subset']:
        qc_data.append(tstep['data'])

    # tidy up data
    dates = [(datetime.datetime(int(date[1:5]), 1, 1) + \
              datetime.timedelta(int(date[5:]))).strftime('%Y-%m-%d') \
              for date in dates]
    sd_data = [y for x in sd_data for y in x]
    qc_data = [y for x in qc_data for y in x]
    df = pd.DataFrame(lai_data, index=dates, columns=['LAI'])
    df["LAI_SD"] = sd_data
    df["QA"] = qc_data

    return df

def build_date_list(start_year, end_year):

    dates = []
    for year in range(start_year, end_year):
        for start in range(1, 365, 8):
            if start + 80 > 365:
                end = 365
            else:
                end = start + 80

            date = "A%4d%03d" % (year, start)
            dates.append( date )

    return dates

def build_request(url, prod, lat, lon, band, dates, dt1, dt2, above_below,
                  left_right):

    request_url = ( url+prod+"/subset?latitude="+str(lat)+"&longitude="+
                   str(lon)+"&band="+band+"&startDate="+dates[dt1]+
                   "&endDate="+dates[dt2]+"&kmAboveBelow="+str(above_below)+
                   "&kmLeftRight="+str(left_right) )

    return request_url

if __name__ == "__main__":

    url = "https://modis.ornl.gov/rst/api/v1/"
    header = {'Accept': 'text/json'}
    lat = 44.4523
    lon = -121.5574
    prod = 'MCD15A2H' # MODIS product
    band = 'Lai_500m'
    sd_band = "LaiStdDev_500m"
    qc_band = 'FparLai_QC'
    above_below = 0 # km above/below
    left_right = 0 # km left/right
    start_year = 2003
    end_year = 2004
    df = main(url, header, lat, lon, prod, band, sd_band, qc_band, above_below,
              left_right, start_year, end_year)

    print(df)
