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

def main(url, header, lat, lon, prod, data_band, qc_band, above_below,
         left_right, start_year, end_year):

    dates = build_date_list(start_year, end_year)

    #******* TESTING REMOVE **********#
    dates = dates[0:25]

    lai_data = []
    qc_data = []

    # loop in increments of 10 so we don't crash the server
    for dt in range(0, len(dates) - 10, 10):

        # Build LAI request url and submit request
        requestURL = ( url+prod+"/subset?latitude="+str(lat)+"&longitude="+
                       str(lon)+"&band="+data_band+"&startDate="+dates[dt]+
                       "&endDate="+dates[dt+9]+"&kmAboveBelow="+
                       str(above_below)+"&kmLeftRight="+str(left_right) )
        response = requests.get(requestURL, headers=header)

        # Loop through list of dictionaries inside the subset key of the
        # response and append data to lai_data
        scale = float(json.loads(response.text)['scale'])
        for tstep in json.loads(response.text)['subset']:
            vals = tstep['data']
            vals = [i*scale for i in vals]
            lai_data.append(vals)

        # Build QC request url and submit request
        requestURL = ( url+prod+"/subset?latitude="+str(lat)+"&longitude="+
                       str(lon)+"&band="+qc_band+"&startDate="+dates[dt]+
                       "&endDate="+dates[dt+9]+"&kmAboveBelow="+
                       str(above_below)+"&kmLeftRight="+str(left_right) )
        response = requests.get(requestURL, headers=header)

        # Loop through list of dictionaries inside the subset key of the
        # response and append data to qc_data
        for tstep in json.loads(response.text)['subset']:
            qc_data.append(tstep['data'])

    # We may still have dates left over. Submit requests for the last <=10
    # dates.

    # Build LAI request url and submit request
    requestURL = ( url+prod+"/subset?latitude="+str(lat)+"&longitude="+
                   str(lon)+"&band="+data_band+"&startDate="+dates[dt+10]+
                   "&endDate="+dates[-1]+"&kmAboveBelow="+str(above_below)+
                   "&kmLeftRight="+str(left_right) )
    response = requests.get(requestURL, headers=header)

    # Loop through list of dictionaries inside the subset key of the response
    # and append data to lai_data
    scale = float(json.loads(response.text)['scale'])
    for tstep in json.loads(response.text)['subset']:
        vals = tstep['data']
        vals = [i*scale for i in vals]
        lai_data.append(vals)

    # Build QC request url and submit request
    requestURL = ( url+prod+"/subset?latitude="+str(lat)+"&longitude="+str(lon)+
                   "&band="+qc_band+"&startDate="+dates[dt+10]+"&endDate="+
                   dates[-1]+"&kmAboveBelow="+str(above_below)+"&kmLeftRight="+
                   str(left_right) )
    response = requests.get(requestURL, headers=header)

    # Loop through list of dictionaries inside the subset key of the response
    # and append data to qc_data
    for tstep in json.loads(response.text)['subset']:
        qc_data.append(tstep['data'])

    # tidy up data
    dates = [(datetime.datetime(int(date[1:5]), 1, 1) + \
              datetime.timedelta(int(date[5:]))).strftime('%Y-%m-%d') \
              for date in dates]
    qc_data = [y for x in qc_data for y in x]
    df = pd.DataFrame(lai_data, index=dates, columns=['LAI'])
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

if __name__ == "__main__":

    url = "https://modis.ornl.gov/rst/api/v1/"
    header = {'Accept': 'text/json'} 
    lat = 44.4523
    lon = -121.5574
    prod = 'MCD15A2H' # MODIS product
    data_band = 'Lai_500m' # band name
    qc_band = 'FparLai_QC' # QC band name
    above_below = 0 # km above/below
    left_right = 0 # km left/right
    start_year = 2003
    end_year = 2004
    df = main(url, header, lat, lon, prod, data_band, qc_band, above_below,
              left_right, start_year, end_year)

    print(df)
