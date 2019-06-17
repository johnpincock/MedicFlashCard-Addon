# -*- coding: utf-8 -*-
import urllib2
# from datetime import datetime -- trying to figure out how to do dates programatically because of inconsistancy in the websites
import requests
from bs4 import BeautifulSoup
import csv
import re, datetime
from datetime import date
import datefinder
from time import gmtime, strftime


def writeCVSFile():
    with open('info.csv', 'w') as csv_file:
        writer = csv.writer(csv_file)
        categoryTitles = 'post_id','post_title','post_author','post_content','post_category','default_category','post_tags','post_type','post_status','is_featured','post_date','post_address','post_city','post_region','post_country','post_zip','post_latitude','post_longitude','geodir_timing','geodir_contact','geodir_email','geodir_website','geodir_twitter','geodir_facebook','geodir_video','geodir_special_offers','linked_cpt_ID','geodir_Compensation','geodir_tiralStart','geodir_trialEnd','IMAGE','IMAGE','IMAGE','IMAGE','IMAGE'
        writer.writerow(categoryTitles)

# this function is for weneedyou.com
# look at the date, i think i can fix this now with some tinkering with datefinder package
def weNeedYou():
    urlLinks = []
    dataSet = []

    page = requests.get("https://www.weneedyou.co.uk/current-trials/")
    soup = BeautifulSoup(page.content, 'xml')
    trialTitle = soup.find_all(class_='tri-TrialItem_Title')
    for b in soup.find_all(class_='tri-TrialItem', href=True):
        urlLinks.append(b['href'])
    string = 'https://www.weneedyou.co.uk'
    fixedUrlLinks = [ string + x for x in urlLinks ]

    for url in fixedUrlLinks:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")
        
        post_id = ''
        trialID = soup.find('p', class_='tri-Article_Highlight').get_text()
        title = soup.find("h1", class_= 'tri-Article_Title').get_text()
        post_title = str(title) + " " + str(trialID)
        post_author = '1'
        profile = soup.find_all('li', class_="lst-Ticks_Item")
        list = []
        for x in profile:
         prof = x.get_text()
         list.append(prof)
        finalList = map(str, list)
        addMoreContentToPost = soup.find('p', class_='tri-Article_Text')
        post_content = "Criteria are:" + '\n'.join(finalList)
        post_category = 'Paid'
        default_category = 'Paid'
        post_tags = ''
        post_type = 'gd_place'
        post_status = 'publish'
        is_featured = ''
        post_date = strftime("%Y-%m-%d %H:%M:%S", gmtime())
        post_address = 'TBC'
        post_city = 'TBC'
        post_region = 'TBC'
        post_country = 'TBC'
        post_zip = 'TBC'
        post_latitude = 'TBC'
        post_longitude = 'TBC'
        geodir_timing = ''
        geodir_contact = 'TBC'
        geodir_email = 'TBC'
        geodir_website = url
        geodir_twitter = ''
        geodir_facebook = ''
        geodir_video = ''
        geodir_special_offers = ''
        linked_cpt_ID = ''
         # who would have thought getting the cost would be so hard !
        cost = soup.find('div', class_='tri-Article_Section').p.text.strip()
        c = cost.encode('utf-8')
        finalCost = int(filter(str.isdigit, c))
        if len(str(finalCost)) == 8:
            geodir_Compensation = finalCost % 10000
        elif len(str(finalCost)) == 7:
            geodir_Compensation = finalCost % 10000
        else:
            geodir_Compensation = finalCost
        date = soup.find_all('p', class_='tri-ArticleSchedule_Time')
        #dateFixed = datetime.strptime(%S , '%b %d %Y %I:%M%p') % date
        dates = []
        for x in date:
         day = x.get_text()
         dates.append(day)
        geodir_tiralStart = dates[0]
        geodir_trialEnd = dates[-1]
        IMAGE = ''
        IMAGE = ''
        IMAGE = ''
        IMAGE = ''
        IMAGE = ''
         
        dataSet = post_id, post_title, post_author, post_content, post_category, default_category,post_tags,post_type,post_status,is_featured,post_date,post_address,post_city,post_region,post_country,post_zip,post_latitude,post_longitude,geodir_timing,geodir_contact,geodir_email,geodir_website,geodir_twitter,geodir_facebook,geodir_video,geodir_special_offers,linked_cpt_ID,geodir_Compensation,geodir_tiralStart,geodir_trialEnd,IMAGE,IMAGE,IMAGE,IMAGE,IMAGE
    

        with open('info.csv', 'a') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(dataSet)

# look at the styling tags in the comment section
def paraxel():
    urlLinks = []
    dataSet = []
    
    page = requests.get("https://www.drugtrial.co.uk/locations/london/en/find-study/available_studies")
    soup = BeautifulSoup(page.content, 'xml')
    results = soup.find_all('td', class_='study_number')
    for a in results:
        links = a.parent['data-url']
        urlLinks.append(links)
    fixedUrlLinks = map(str, urlLinks)
    for url in fixedUrlLinks:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")
        post_id = ''
        post_title = soup.find('h2', class_='title').get_text()
        post_author = '1'
        additionalContent = soup.find('span', class_='additional_info').p
        cnt = soup.find('div', class_='gray_bkd').get_text()
        post_content = str(cnt) + str(additionalContent)
        post_category = 'Paid'
        default_category = 'Paid'
        post_tags = ''
        post_type = 'gd_place'
        post_status = 'publish'
        is_featured = ''
        post_date = strftime("%Y-%m-%d %H:%M:%S", gmtime())
        post_address = 'Northwick Park Hospital'
        post_city = 'Harrow'
        post_region = 'Greater London'
        post_country = 'United Kingdom'
        post_zip = 'HA1 3GX'
        post_latitude = '51.5751501'
        post_longitude = '-0.319518099999982'
        geodir_timing = ''
        geodir_contact = '0800 389 8930'
        geodir_email = 'drugtrial@PAREXEL.com'
        geodir_website = url
        geodir_twitter = ''
        geodir_facebook = ''
        geodir_video = ''
        geodir_special_offers = ''
        linked_cpt_ID = ''
        # who would have thought getting the cost would be so hard !
        cost = soup.find('p', class_='value study_compensation').text.strip()
        c = cost.encode('utf-8')
        finalCost = int(filter(str.isdigit, c))
        if len(str(finalCost)) == 8:
            geodir_Compensation = finalCost % 10000
        elif len(str(finalCost)) == 7:
            geodir_Compensation = finalCost % 10000
        else:
            geodir_Compensation = finalCost
        dating = soup.find('div', class_='dates')
        fixedDates = dating.get_text()
        d = fixedDates.replace('-', '$')
        matches = datefinder.find_dates(d)
        date = []
        for match in matches:
            date.append(str(match))


        geodir_tiralStart = date[0]
        endDate = date[-1]
        if endDate == geodir_tiralStart:
            endDate = ''
        else:
            endDate = date[-1]
        geodir_trialEnd = endDate
        IMAGE = ''
        IMAGE = ''
        IMAGE = ''
        IMAGE = ''
        IMAGE = ''
        
        dataSet = post_id, post_title, post_author, post_content, post_category, default_category,post_tags,post_type,post_status,is_featured,post_date,post_address,post_city,post_region,post_country,post_zip,post_latitude,post_longitude,geodir_timing,geodir_contact,geodir_email,geodir_website,geodir_twitter,geodir_facebook,geodir_video,geodir_special_offers,linked_cpt_ID,geodir_Compensation,geodir_tiralStart,geodir_trialEnd,IMAGE,IMAGE,IMAGE,IMAGE,IMAGE
        
        
        with open('info.csv', 'a') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(dataSet)

def londonTrials():
    urlLinks = []
    dataSet = []
    
    page = requests.get("https://www.londontrials.com/jobs")
    soup = BeautifulSoup(page.content, 'lxml')
    results = soup.find_all('div', class_='txt')
    for result in results:
        data = result.parent
        dataSet.append(data)
    for data in dataSet:
        post_id = ''
        post_title = data.find('strong').get_text()
        post_author = '1'
        content = data.find('div', class_='txt').get_text()
        additionalContent = data.find('h3').parent.parent.p.get_text()
        moreInfo = additionalContent.encode('utf-8').strip()
        post_content = content.encode('utf-8').strip() + '\n' + "Compensation for this trial is " + moreInfo
        print post_content
        post_category = 'Paid'
        default_category = 'Paid'
        post_tags = ''
        post_type = 'gd_place'
        post_status = 'publish'
        is_featured = ''
        post_date = strftime("%Y-%m-%d %H:%M:%S", gmtime())
        post_address = 'Cumberland Avenue'
        post_city = 'London'
        post_region = 'Greater London'
        post_country = 'United Kingdom'
        post_zip = 'NW10'
        post_latitude = '51.5305295'
        post_longitude = '-0.274349700000016'
        geodir_timing = ''
        geodir_contact = '0800 783 8792'
        geodir_email = 'https://www.londontrials.com/jobs'
        website = [a['href'] for a in data.find_all('a', href=True)]
        LTR = "londontrials.com"
        geodir_website = LTR + str(website[0])
        geodir_twitter = ''
        geodir_facebook = ''
        geodir_video = ''
        geodir_special_offers = ''
        linked_cpt_ID = ''
        cost = data.find('h3').parent.parent.p
        c = cost.find(text=True, recursive=False)
        finalCost = int(filter(str.isdigit, c.encode('utf-8')))
        if len(str(finalCost)) == 8:
            geodir_Compensation = finalCost % 10000
        elif len(str(finalCost)) == 7:
            geodir_Compensation = finalCost % 10000
        else:
            geodir_Compensation = finalCost
        geodir_tiralStart = strftime("%Y-%m", gmtime())
        endDate = " "
        geodir_trialEnd = endDate
        IMAGE = ''
        IMAGE = ''
        IMAGE = ''
        IMAGE = ''
        IMAGE = ''
        
        dataSet = post_id, post_title, post_author, post_content, post_category, default_category,post_tags,post_type,post_status,is_featured,post_date,post_address,post_city,post_region,post_country,post_zip,post_latitude,post_longitude,geodir_timing,geodir_contact,geodir_email,geodir_website,geodir_twitter,geodir_facebook,geodir_video,geodir_special_offers,linked_cpt_ID,geodir_Compensation,geodir_tiralStart,geodir_trialEnd,IMAGE,IMAGE,IMAGE,IMAGE,IMAGE
        
        
        with open('info.csv', 'a') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(dataSet)

def TrialsForUs():
    urlLinks = []
    dataSet = []
    
    page = requests.get("http://www.trials4us.co.uk/ongoing-clinical-trials/")
    soup = BeautifulSoup(page.content, 'lxml')
    trialTitle = soup.find_all('div', class_='trials-text-box')
    for b in trialTitle:
        c = b.find('a', href=True)
        urlLinks.append(c['href'])
    for url in urlLinks:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")
        
        post_id = ''
        post_title = soup.find('div', class_='heading-text').h1.text
        post_author = '1'
        content = soup.find('div', class_='content-column two_third').get_text()
        a = soup.find('div', class_='post-content')
        b = a.find_all('ul')
        additionalContent = ''
        for c in b:
            additionalContent = c.get_text()
        post_content = additionalContent.encode('utf-8') + content.encode('utf-8')
        post_category = 'Paid'
        default_category = 'Paid'
        post_tags = ''
        post_type = 'gd_place'
        post_status = 'publish'
        is_featured = ''
        post_date = strftime("%Y-%m-%d %H:%M:%S", gmtime())
        post_address = '1 Newcomen St'
        post_city = 'London'
        post_region = 'Greater London'
        post_country = 'United Kingdom'
        post_zip = 'SE1 1UL'
        post_latitude = '51.5026029'
        post_longitude = '-0.0895867000000408'
        geodir_timing = ''
        geodir_contact = '0800 085 6464'
        geodir_email = 'volunteer@richmondpharmacology.com'
        geodir_website = url
        geodir_twitter = ''
        geodir_facebook = ''
        geodir_video = ''
        geodir_special_offers = ''
        linked_cpt_ID = ''
        forCost = soup.find('div',class_='col-md-9 col-md-push-3').get_text()
        cost = re.findall(r'£(\d+.\d+)', str(forCost.encode('utf-8').strip()))
        if len(cost) == 0:
            c = ""
        elif len(cost) == 1:
            c = cost[0]
        else:
            c = max(cost)
        geodir_Compensation = filter(str.isdigit, c.encode('utf-8'))

        geodir_tiralStart = strftime("%Y-%m", gmtime())
        geodir_trialEnd = ''
        IMAGE = ''
        IMAGE = ''
        IMAGE = ''
        IMAGE = ''
        IMAGE = ''

        dataSet = post_id, post_title, post_author, post_content, post_category, default_category,post_tags,post_type,post_status,is_featured,post_date,post_address,post_city,post_region,post_country,post_zip,post_latitude,post_longitude,geodir_timing,geodir_contact,geodir_email,geodir_website,geodir_twitter,geodir_facebook,geodir_video,geodir_special_offers,linked_cpt_ID,geodir_Compensation,geodir_tiralStart,geodir_trialEnd,IMAGE,IMAGE,IMAGE,IMAGE,IMAGE
    
    
        with open('info.csv', 'a') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(dataSet)

def covanceTrials():
    urlLinks = []
    dataSet = []
    
    #page = requests.get("https://www.covanceclinicaltrials.com/en-gb/browse-studies.html")
    #soup = BeautifulSoup(page.content, 'lxml')
    #trialTitle = soup.find_all('div', class_='trials-text-box')
    i=1
    url = "https://www.covanceclinicaltrials.com/en-gb/browse-studies.html#p?ts=1523106062646&dates=all&displayType=list&pageNumber=%s&studyResults=8" % str(i)
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'lxml')
    link = soup.find_all(class_ = "see-more-title", href=True)

    for b in link:
        c = b.get('href')
        url = "https://www.covanceclinicaltrials.com" + c
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")

        post_id = ''
        post_title = soup.find('div', class_='col_1-2').h2.get_text()
        post_author = '1'
        topDetails = soup.find_all('div', class_="twtb-desktop-list")
        for deet in topDetails:
            a = deet.get_text()
            b = a.replace('  ', '')

            cost = re.findall(r'£(\d+.\d+)', str(b.encode('utf-8').strip()))
            if len(cost) == 0:
                c = ""
            elif len(cost) == 1:
                c = cost[0]
            else:
                c = max(cost)
        post_category = 'Paid'
        default_category = 'Paid'
        post_tags = ''
        post_type = 'gd_place'
        post_status = 'publish'
        is_featured = ''
        post_date = strftime("%Y-%m-%d %H:%M:%S", gmtime())
        post_address = 'TBC'
        post_city = 'TBC'
        post_region = 'TBC'
        post_country = 'TBC'
        post_zip = 'TBC'
        post_latitude = 'TBC'
        post_longitude = 'TBC'
        geodir_timing = ''
        geodir_contact = 'TBC'
        geodir_email = 'TBC'
        geodir_website = url
        geodir_twitter = ''
        geodir_facebook = ''
        geodir_video = ''
        geodir_special_offers = ''
        linked_cpt_ID = ''
        geodir_Compensation = filter(str.isdigit, c.encode('utf-8'))
        date = []
        maxDate = datetime.datetime.today() + datetime.timedelta(days=365)
        today = datetime.date.today()
        dates = soup.find_all('div', class_='row twtb-more-info')
        dating = dates[-1].get_text()
        matches = datefinder.find_dates(dating)
        for match in matches:
            d = match.strftime('%Y-%m-%d')
            b = maxDate.strftime('%Y-%m-%d')
            if d > b:
                continue
            else:
                date.append(d)
        geodir_tiralStart = min(date)
        geodir_trialEnd = max(date)
        IMAGE = ''
        IMAGE = ''
        IMAGE = ''
        IMAGE = ''
        IMAGE = ''







covanceTrials()


