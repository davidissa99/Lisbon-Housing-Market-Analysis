import csv
import random
import time
import json
import requests
import os
from bs4 import BeautifulSoup
from fake_headers import Headers

if not os.path.exists('data'):
    os.mkdir('data/')

with open("data/properties_data_2.csv", "w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(["id", "property-header", "property_description", "num_bedrooms", "price", "net_area_m2", "gross_area_m2", 
                     "construction_year", "locality", "region", "latitude", "longitude"])

    for page in range(1, 535):
        headers = Headers(headers=True).generate()
        time.sleep(random.randint(1, 10))
        url = f"https://casa.sapo.pt/en/buy-apartments/lisboa/?pn={page}"
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, "html.parser")

        properties = soup.findAll("div", class_="property")
        print(f"Page {page} - Propriedades {len(properties)}")
        for i, build in enumerate(properties):
            
            property_link = build.find('a')['href']
            if not property_link.startswith("https"):
                host = "https://casa.sapo.pt/"
                property_link = f"{host}{property_link}"
            property_link_response = requests.get(property_link, headers=headers)
            property_link_soup = BeautifulSoup(property_link_response.content, "html.parser")

            # 1.Property header (publication title)
            property_header = build.find("div", class_="featured-property-header", default=None)   
            if property_header:
                property_header = property_header.text.strip()
            else:
                property_header = None

            # 2.Property description (contains many different information regardin the property)
            property_description = build.find("div", class_="property-description", default=None)
            if property_description:
                property_description = property_description.text.strip()
            else:
                property_description = None
                
            # 3.Property price
            price = build.find("div", class_="property-price-value").text.strip()
            for element in price.split():
                element = element.replace('.','')
                if element.isnumeric() == True:
                    price = element
            
            # 4.Number of bedrooms                       
            for i, feature in enumerate(property_link_soup.findAll("div", {"class": "detail-features-item"})):
                if 'Total quarto(s)' in feature.text.strip():
                    num_bedrooms = feature.text.strip().split()[-1]
                    if num_bedrooms.isnumeric():
                        num_bedrooms = int(num_bedrooms)
                    else:
                        num_bedrooms = None

            # 5.Property area
            features_dict = {}
            for i, feature in enumerate(property_link_soup.findAll("div", {"class": "detail-main-features-item"})):
                features_dict[feature.find("div", {"class": "detail-main-features-item-title"}).text.strip()] = feature.find("div", {"class": "detail-main-features-item-value"}).text.strip()
 
            if 'Área útil' in list(features_dict.keys()):
                net_area_m2 = features_dict['Área útil']
                net_area_m2 = int(net_area_m2.replace('m²', '').replace('\xa0', ''))
            else:
                net_area_m2 = None
                
            if 'Área bruta' in list(features_dict.keys()):
                gross_area_m2 = features_dict['Área bruta']
                gross_area_m2 = int(gross_area_m2.replace('m²', '').replace('\xa0', ''))
            else:
                gross_area_m2 = None
            
            # 5. Year of construction
            if 'Ano de construção' in list(features_dict.keys()):
                construction_year = int(features_dict['Ano de construção'])
            else:
                construction_year = None

     
            script = build.find('script', {'type': 'application/ld+json'}).string
            data = json.loads(script)
            
            # 6.Property locality
            locality = data.get('availableAtOrFrom', {}).get('address', {}).get('addressLocality', None)
            if locality:
                locality = locality.replace('\n', ' ')
                
            # 7.Property region
            region = data.get('availableAtOrFrom', {}).get('address', {}).get('addressRegion', None)
            if region:
                region = region.replace('\n', ' ')
                
            # 8.Property coordinates
            latitude = data.get('availableAtOrFrom', {}).get('geo', {}).get('latitude', None)
            longitude = data.get('availableAtOrFrom', {}).get('geo', {}).get('longitude', None)
            
            #write all extracted features to csv file
            category = data.get('category', None)
            writer.writerow([page*1000 + i, property_header, property_description, num_bedrooms, price, net_area_m2,
                             gross_area_m2, construction_year, locality, region, latitude, longitude])
