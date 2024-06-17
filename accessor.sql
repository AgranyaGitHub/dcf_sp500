CREATE DATABASE stock_data;
\c stock_data

CREATE TABLE stock_data (
    id SERIEAL PRIMARY KEY,
    ticker VARCHAR(10),
    compName TEXT
)