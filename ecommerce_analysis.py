# -*- coding: utf-8 -*-
"""Ecommerce analysis.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1qf1ecKUfVEUXr1r9DOKSAVbH8BWB277B
"""

import pandas as pd
from google.colab import drive
drive.mount('/content/drive')
fact_orders_raw=pd.read_csv('/content/drive/MyDrive/cleaned_retail_data_293k.csv')
fact_orders_raw['Date']=pd.to_datetime(fact_orders_raw['Date'])

fact_orders_raw.info()

dim_customers=fact_orders_raw.iloc[:,1:14]
dim_customers.rename(columns={"Income": "Income_Level"},inplace=True)
dim_customers.drop_duplicates(inplace=True, ignore_index=False)
dim_customers

fact_orders_raw.drop(fact_orders_raw.columns[2:14], axis=1, inplace=True)

dim_products=fact_orders_raw.iloc[:,9:13].sort_values(['Product_Category',
                                                       'Product_Brand',
                                                       'Product_Type',
                                                       'products'],
                                                      axis=0,
                                                      ascending=[True,
                                                                 True,
                                                                 True,
                                                                 True])
dim_products.drop_duplicates(ignore_index=True,inplace=True)
dim_products

import numpy as np
product_code = np.arange(1,481, dtype=np.int64)
product_code_list = list(product_code)
dim_products['Product_Code']=product_code_list
dim_products

dim_products['Product_Consol']=dim_products['Product_Category']+dim_products['Product_Brand']+dim_products['Product_Type']+dim_products['products']
fact_orders_raw['Product_Consol']=fact_orders_raw['Product_Category']+fact_orders_raw['Product_Brand']+fact_orders_raw['Product_Type']+fact_orders_raw['products']
fact_orders_raw.drop(['Product_Category','Product_Brand','Product_Type','products'], axis=1, inplace=True)
fact_orders=pd.merge(left=fact_orders_raw,
                           right=dim_products,
                           how='left',
                           left_on=fact_orders_raw['Product_Consol'],
                           right_on=dim_products['Product_Consol'])
fact_orders.drop(['Product_Category',
                  'Product_Brand',
                  'Product_Type',
                  'products',
                  'key_0',
                  'Product_Consol_x',
                  'Product_Consol_y'], axis=1, inplace=True)
dim_products.drop(['Product_Consol'], axis=1, inplace=True)
dim_products

fact_orders.to_csv('fact_orders.csv',index=False)
dim_customers.to_csv('dim_customers.csv',index=False)
dim_products.to_csv('dim_products.csv',index=False)

cust_score=fact_orders.groupby('Customer_ID').agg({'Date':'max',
                                                   'Transaction_ID':'nunique',
                                                   'Total_Amount':'sum'}).reset_index()
cust_score['Date']=pd.to_datetime(cust_score['Date'])
cust_score

def diff_date(data):
  return abs(cust_score['Date'].max().date()-data['Date'].date()).days

cust_score['R']=cust_score.apply(diff_date, axis=1)
cust_score

cust_score.drop(columns=['Date'],inplace=True)
cust_score.rename(columns={'Transaction_ID':'F','Total_Amount':'M'},inplace=True)
cust_score

r_80=cust_score['R'].quantile(0.8)
r_60=cust_score['R'].quantile(0.6)
r_40=cust_score['R'].quantile(0.4)
r_20=cust_score['R'].quantile(0.2)
f_80=cust_score['F'].quantile(0.8)
f_60=cust_score['F'].quantile(0.6)
f_40=cust_score['F'].quantile(0.4)
f_20=cust_score['F'].quantile(0.2)
m_80=cust_score['M'].quantile(0.8)
m_60=cust_score['M'].quantile(0.6)
m_40=cust_score['M'].quantile(0.4)
m_20=cust_score['M'].quantile(0.2)

def r_score(data):
  if data['R']>=r_80:
    return '1'
  elif data['R']>=r_60:
    return '2'
  elif data['R']>=r_40:
    return '3'
  elif data['R']>=r_20:
    return '4'
  else:
    return '5'

def f_score(data):
  if data['F']>=f_80:
    return '5'
  elif data['F']>=f_60:
    return '4'
  elif data['F']>=f_40:
    return '3'
  elif data['F']>=f_20:
    return '2'
  else:
    return '1'

def m_score(data):
  if data['M']>=m_80:
    return '5'
  elif data['M']>=m_60:
    return '4'
  elif data['M']>=m_40:
    return '3'
  elif data['M']>=m_20:
    return '2'
  else:
    return '1'

cust_score['R_score']=cust_score.apply(r_score,axis=1)
cust_score['F_score']=cust_score.apply(f_score,axis=1)
cust_score['M_score']=cust_score.apply(m_score,axis=1)
cust_score['Total_Score']=cust_score['R_score']+cust_score['F_score']+cust_score['M_score']
cust_score['Total_Score']=cust_score['Total_Score'].astype(int)
cust_score.info()

rfm_ref=pd.read_csv('/content/drive/MyDrive/RankRFM.csv')

# Split text into a list
rfm_ref['Scores'] = rfm_ref['Scores'].str.split(',')
# Convert list into multiple rows
rfm_ref = rfm_ref.explode('Scores')
rfm_ref['Scores']=rfm_ref['Scores'].astype(int)

dim_cust_type_rfm=pd.merge(
    left=cust_score,
    right=rfm_ref,
    how='left',
    left_on=cust_score['Total_Score'],
    right_on=rfm_ref['Scores'])
dim_cust_type_rfm.drop(columns=['Scores','key_0'],inplace=True)
dim_cust_type_rfm

cust_type=dim_cust_type_rfm[['Customer_ID','Segment']]
cust_type

dim_cust_type_rfm.to_csv('dim_cust_type_rfm.csv',index=False)

fact_orders['Invoice_Month']=fact_orders['Date'].dt.to_period('M')
fact_orders

fact_orders['Cohort_Month']=fact_orders.groupby('Customer_ID')['Invoice_Month'].transform('min')
fact_orders

def month_diff(data):
  return (data['Invoice_Month'].year-data['Cohort_Month'].year)*12+(data['Invoice_Month'].month-data['Cohort_Month'].month)

fact_orders['Month_Diff']=fact_orders.apply(month_diff,axis=1)
fact_orders

cohort_table = fact_orders.groupby(['Cohort_Month', 'Month_Diff']).agg(n_customers = ('Customer_ID', 'nunique')).reset_index()
cohort_table

dim_customers_seg=dim_customers[['Customer_ID','Customer_Loyalty']]

fact_orders_segment=pd.merge(
    left=fact_orders,
    right=dim_customers_seg,
    how='left',
    left_on=fact_orders['Customer_ID'],
    right_on=dim_customers_seg['Customer_ID'])
fact_orders_segment.drop(columns=['key_0','Customer_ID_y'],inplace=True)
fact_orders_segment.rename(columns={"Customer_ID_x": "Customer_ID"},inplace=True)
fact_orders_segment

"""**New**"""

fact_orders_new=fact_orders_segment[fact_orders_segment['Customer_Loyalty']=='New']
fact_orders_new.drop(columns=['Invoice_Month','Cohort_Month','Month_Diff'],inplace=True)
fact_orders_new['Invoice_Month']=fact_orders_new['Date'].dt.to_period('M')
fact_orders_new['Cohort_Month']=fact_orders_new.groupby('Customer_ID')['Invoice_Month'].transform('min')
fact_orders_new['Month_Diff']=fact_orders_new.apply(month_diff,axis=1)
cohort_table_new = fact_orders_new.groupby(['Cohort_Month', 'Month_Diff']).agg(n_customers = ('Customer_ID', 'nunique')).reset_index()

"""**Regular**"""

fact_orders_regular=fact_orders_segment[fact_orders_segment['Customer_Loyalty']=='Regular']
fact_orders_regular.drop(columns=['Invoice_Month','Cohort_Month','Month_Diff'],inplace=True)
fact_orders_regular['Invoice_Month']=fact_orders_regular['Date'].dt.to_period('M')
fact_orders_regular['Cohort_Month']=fact_orders_regular.groupby('Customer_ID')['Invoice_Month'].transform('min')
fact_orders_regular['Month_Diff']=fact_orders_regular.apply(month_diff,axis=1)
cohort_table_regular = fact_orders_regular.groupby(['Cohort_Month', 'Month_Diff']).agg(n_customers = ('Customer_ID', 'nunique')).reset_index()

"""**Premium**"""

fact_orders_premium=fact_orders_segment[fact_orders_segment['Customer_Loyalty']=='Premium']
fact_orders_premium.drop(columns=['Invoice_Month','Cohort_Month','Month_Diff'],inplace=True)
fact_orders_premium['Invoice_Month']=fact_orders_premium['Date'].dt.to_period('M')
fact_orders_premium['Cohort_Month']=fact_orders_premium.groupby('Customer_ID')['Invoice_Month'].transform('min')
fact_orders_premium['Month_Diff']=fact_orders_premium.apply(month_diff,axis=1)
cohort_table_premium = fact_orders_premium.groupby(['Cohort_Month', 'Month_Diff']).agg(n_customers = ('Customer_ID', 'nunique')).reset_index()

cohort_table.to_csv('cohort_table.csv',index=False)
cohort_table_new.to_csv('cohort_table_new.csv',index=False)
cohort_table_regular.to_csv('cohort_table_regular.csv',index=False)
cohort_table_premium.to_csv('cohort_table_premium.csv',index=False)
