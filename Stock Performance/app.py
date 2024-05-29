import numpy as np
import pandas as pd
import yfinance as yf 
import streamlit as st
from datetime import datetime, timedelta
import plotly_express as px
from streamlit_datetime_range_picker import datetime_range_picker
from st_aggrid import AgGrid
import altair as alt
import plotly.graph_objs as go
from streamlit_option_menu import option_menu
import time
from menu import menu
import hmac

#Title
#st.write("This web application create tools for finding your port performance. Created by JoeNamluck")

#Add sidebar
def set_page_config():
    st.set_page_config(
        page_title="Stock Indicator",
        layout="wide",
        initial_sidebar_state="collapsed",
        
        )
    
    with st.sidebar:
        selected = option_menu("Performance", ["Home", 'Setting'], 
        icons=['house', 'gear'], menu_icon="cast", default_index=1)
                    # Initialize st.session_state.role to None
        if "role" not in st.session_state:
            st.session_state.role = None

        # Retrieve the role from Session State to initialize the widget
        st.session_state._role = st.session_state.role

        def set_role():
            # Callback function to save the role selection to Session State
            st.session_state.role = st.session_state._role


        # Selectbox to choose role
        st.selectbox(
            "Select your role:",
            [None, "user", "admin", "super-admin"],
            key="_role",
            on_change=set_role,
        )
        menu() # Render the dynamic menu!
    
    selected
    
        
def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if hmac.compare_digest(st.session_state["password"], st.secrets["password"]):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store the password.
        else:
            st.session_state["password_correct"] = False

    # Return True if the password is validated.
    if st.session_state.get("password_correct", False):
        return True

    # Show input for password.
    st.text_input(
        "Password", type="password", on_change=password_entered, key="password"
    )
    if "password_correct" in st.session_state:
        st.error("😕 Password incorrect")
    return False

        
#list of S&P500 stock to compare
def select_stock(options_stock_to_pick):
    options = st.multiselect(
        "What stock do you have in your portfolio?",
        options_stock_to_pick)

    return options
      


def stream_data():
    _LOREM_IPSUM = """
    This dashboard created by Joe Namluck. Creating this dashboard
    give ability to track how your portfoilio doing verses all 
    benchmarks out there! If you are better than benchmark, you are 
    doing great. If not you might need to start thinking buying 
    index ETF.
    
    Goodluck!
    """

    for word in _LOREM_IPSUM.split(" "):
        yield word + " "
        time.sleep(0.1)

def obtain_data_stock(stock_name,start_date,end_date):
# Benchmark to compare
    df_index=yf.download(stock_name,start=start_date,end=end_date)
    data_index=df_index['Close']

    #select  only last day of each month
    data_index_sort=data_index.sort_index().resample("M").apply(lambda ser: ser.iloc[-1,])

    return data_index_sort

def ticker_stock(tickers,start_date,end_date):

    if len(tickers)==1:
        df=pd.DataFrame()
        df_temp=yf.download(tickers,start=start_date,end=end_date)
        df_temp_sort=df_temp['Adj Close']
        df=df_temp_sort
    
    else:
        df=pd.DataFrame()    
        for ticker in tickers:    
            df_temp=yf.download(tickers,start=start_date,end=end_date)
            df_temp_sort=df_temp['Adj Close']
            df=pd.concat([df,df_temp_sort])
    return df

#calculate performance at that month
def performance_month(index_data,start_date,stock):
    #write to compare to previous month before investing
    first = start_date
    last_month = first - timedelta(days=1)
    last_month_first=last_month-timedelta(days=30)

    pull_last=yf.download(stock,start=last_month_first,end=last_month)
    pull_last_s=pull_last['Close']

    pull_last_sort=pull_last_s.sort_index().resample("M").apply(lambda ser: ser.iloc[-1,])
    compare_last=pull_last_sort.iloc[0]

    #compare to get performance in percentage
    percent_change_index=[]
    for i in range(len(index_data)-1):
        previous=index_data.iloc[i]
        i=i+1
        next=index_data.iloc[i]
        percent=((next - previous) / previous) * 100.0
        percent_change_index.append(round(percent,2))
            
    first_month=((index_data.iloc[0]-compare_last)/compare_last)*100
    first_month_round=round(first_month,2)
    percent_change_final=percent_change_index.insert(0,first_month_round)


    data_show_index=pd.DataFrame(index_data)

    data_show_index.rename({data_show_index.index[-1]:datetime.now()},inplace=True)


    #append to data of index we want to compare
    data_show_index.insert(1,"performance",percent_change_index)

    return data_show_index



#calculate performace each year
def calculate_performance(stock_data):
    total=1
    for i in range(len(stock_data)-1):
        month_percent=1+((stock_data.iat[i,1])/100)
        total*=month_percent
        
    performance_in_a_year=round((total-1)*100,2)
    return performance_in_a_year

#computing cumulative return
def cum_return(dataframe):
    df_daily_returns=dataframe.pct_change()
    df_daily_returns=df_daily_returns[1:]
    
    df_cum_daily_returns = (1 + df_daily_returns).cumprod() - 1
    df_cum_daily_returns = df_cum_daily_returns.reset_index()
    
    return df_cum_daily_returns

def daily_return(dataframe):
    df_daily_returns=dataframe.pct_change()
    df_daily_returns=df_daily_returns[1:]
    
    return df_daily_returns

#metric indicate 
def metric(data_to_show,performance):
    col1, col2,col3, col4 = st.columns(4)
    data_show_metric=data_to_show.tail()
    data_show_index_last=data_show_metric.iloc[-1]

    col1.metric("Benchmark", str(performance)+'%', str(data_show_index_last.iloc[-1])+' last month')
    col3.metric("My Port", "+17.00%", "+8%")

# saving the excel
#file_name = 'PG.xlsx'
def save_to_excel(file_name):    
    file_name.to_excel(file_name)


##############################################################
############### data show in web application##################
##############################################################

def main():
    set_page_config()
    

    if not check_password():
        st.stop()  # Do not continue if check_password is not True.

    # Main Streamlit app starts here
    st.write("Here goes your normal Streamlit app...")
    st.button("Click me")
    
    
    
    
    stock_options=pd.read_csv('SP500.csv')
    select_stock_option=[]
    for i in range(len(stock_options)):
        select_stock_option.append(stock_options)
    select_stock_option_df=pd.DataFrame(data=stock_options, columns=['Symbol','Name','Sector'])
    
    #####################First Row#######################
    col1, col2, col3 = st.columns(3)
    
    # Select Date
    max_date=datetime.now()
    max=max_date.date()
    
    with col1:
        # Create a datetime slider with a range of one week
        start_date = st.date_input("Date you start investing",value=datetime(2000, 1, 1),max_value=max)
        end_date = start_date + timedelta(weeks=2095)

        #change from datetype to date
        today=datetime.now()
        end=today.date()
        
        with st.expander("Select date range"):
            #Slider config
            selected_date = st.slider(
                "Select a date range",
                min_value=start_date,
                max_value=end,
                value=(start_date, end),
                step=timedelta(days=1),
            )
        
    with col2:
        options=select_stock(select_stock_option_df)
        @st.experimental_dialog("Stock Record")
        
        def vote(item):
            st.write(f" {item}ing stock record")
            reason = st.text_input("Because...")
            select_stock
            if st.button("Submit"):
                st.session_state.vote = {"item": item, "reason": reason}
                select_stock
                st.rerun()
        
        col5,col6,col7,col8=st.columns(4)    
        if "vote" not in st.session_state:
            with col5:
                if st.button("Buy"):
                    vote("Buy")
            with col6:
                if st.button("Sell"):
                    vote("Sell")
        else:
            f"You voted for {st.session_state.vote['item']} because {st.session_state.vote['reason']}"
       
        
    
    with col3:
        
        tickers=options
        
        data_show_ticker=ticker_stock(tickers,selected_date[0],end)
        
        if len(options)==0:
            st.write(' ')
            
        elif len(options)==1:
            
            df_cum_return_one=cum_return(data_show_ticker)
    
        else:
            df_cum_return_many=cum_return(data_show_ticker)
            

    
    #####################First Row####################### 

    #data_clean=obtain_data_stock("^GSPC",selected_date[0],end_date)
    
    #data_index_ready_to_show=performance_month(data_clean,selected_date[0],"^GSPC")
   
    #performance=calculate_performance(data_index_ready_to_show)

    #metric(data_index_ready_to_show,performance)
        
    #####################Second Row#######################     
    col1, col2, col3 = st.columns(3)
    with col1:
        #st.dataframe(data_index_ready_to_show,height=200,width=320,column_config={
        #"Date":"Date",
        #"Close":"Close",
        #"performance":"Performance"
        #})
        if len(options)==0:
            st.write(stream_data)
            
        elif len(options)==1:
            st.dataframe(df_cum_return_one,height=300,width=320,hide_index=True)
            
            
        else:
            #show=pd.concat([df_cum_return,df_cum_return_pct])
            st.dataframe(df_cum_return_many,height=300,width=320,hide_index=True
                        ,column_config={"Date":"Date"
            })
                
            
        
    with col2:
        if len(options)==0:
            st.write(' ')
        elif len(options)==1:
            plot=px.line(data_frame=df_cum_return_one, x='Date',y='Adj Close',
                        title='Performance of the stock',
            labels={'cum_return_pct':'daily cumulative returns (%)', })

            st.plotly_chart(plot,theme="streamlit")
        else:
            plot=px.line(data_frame=df_cum_return_many, x='Date', y=options,
                            title='Performance - Daily Cumulative Returns',
                labels={'cum_return_pct':'daily cumulative returns (%)', })

            st.plotly_chart(plot)

        
        
        
    #####################Second Row#######################        
        


if __name__=='__main__':
    main()
    


 
    

