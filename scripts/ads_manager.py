"""
Google Ads Manager Script
Integrated tool for managing campaigns, ad groups, and ads

Run with: ddev exec python scripts/ads_manager.py <command> [OPTIONS]

Commands:
  campaign list   - List campaigns
  campaign create - Create new campaign
  campaign update - Update existing campaign
  adgroup list    - List ad groups
  adgroup create  - Create new ad group
  adgroup update  - Update existing ad group
  ad list         - List ads
  ad create       - Create new ad
  ad update       - Update existing ad
"""

import os
import sys
import argparse
from datetime import datetime
import csv

# Add the parent directory to sys.path to import src modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.config import REPORTS_DIR, get_google_ads_client
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
from google.ads.googleads.v17.enums.types import (
    CampaignStatusEnum, AdGroupStatusEnum, AdGroupAdStatusEnum,
    AdvertisingChannelTypeEnum, CampaignBudgetPeriodEnum
)

def setup_client():
    return get_google_ads_client()

# Campaign Management Functions

def list_campaigns(client, customer_id, status=None):
    googleads_service = client.get_service("GoogleAdsService")
    query = """
        SELECT 
            campaign.id, 
            campaign.name, 
            campaign.status,
            campaign.start_date,
            campaign.end_date,
            campaign.advertising_channel_type
        FROM campaign
    """
    if status:
        query += f" WHERE campaign.status = '{status.upper()}'"
    
    response = googleads_service.search(customer_id=str(customer_id), query=query)
    return [row.campaign for row in response]

def create_campaign(client, customer_id, name, budget_amount, channel_type='SEARCH', status='PAUSED', start_date=None, end_date=None):
    campaign_service = client.get_service("CampaignService")
    budget_service = client.get_service("CampaignBudgetService")
    
    # Create budget
    budget_op = client.get_type("CampaignBudgetOperation")
    budget = budget_op.create
    budget.name = f"Budget for {name} {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    budget.amount_micros = budget_amount * 1_000_000
    budget.delivery_method = client.enums.BudgetDeliveryMethodEnum.STANDARD
    budget.period = CampaignBudgetPeriodEnum.DAILY
    
    budget_response = budget_service.mutate_campaign_budgets(customer_id=str(customer_id), operations=[budget_op])
    budget_resource = budget_response.results[0].resource_name
    
    # Create campaign
    campaign_op = client.get_type("CampaignOperation")
    campaign = campaign_op.create
    campaign.name = name
    campaign.status = getattr(CampaignStatusEnum, status.upper())
    campaign.advertising_channel_type = getattr(AdvertisingChannelTypeEnum, channel_type.upper())
    campaign.campaign_budget = budget_resource
    if start_date:
        campaign.start_date = start_date
    if end_date:
        campaign.end_date = end_date
    campaign.manual_cpc = client.get_type("ManualCpc")
    
    response = campaign_service.mutate_campaigns(customer_id=str(customer_id), operations=[campaign_op])
    return response.results[0].resource_name

def update_campaign(client, customer_id, campaign_id, name=None, status=None, budget_amount=None):
    campaign_service = client.get_service("CampaignService")
    googleads_service = client.get_service("GoogleAdsService")
    
    campaign = client.get_type("Campaign")
    campaign.resource_name = googleads_service.campaign_path(customer_id, campaign_id)
    
    if name:
        campaign.name = name
    if status:
        campaign.status = getattr(CampaignStatusEnum, status.upper())
    # For budget, would need to update the associated budget
    
    op = client.get_type("CampaignOperation")
    op.update = campaign
    op.update_mask = client.get_type("FieldMask")
    paths = []
    if name: paths.append("name")
    if status: paths.append("status")
    client.copy_from(op.update_mask, paths)
    
    response = campaign_service.mutate_campaigns(customer_id=str(customer_id), operations=[op])
    return response.results[0].resource_name

# Ad Group Management Functions

def list_ad_groups(client, customer_id, campaign_id=None, status=None):
    googleads_service = client.get_service("GoogleAdsService")
    query = """
        SELECT 
            ad_group.id, 
            ad_group.name, 
            ad_group.status,
            campaign.id,
            campaign.name
        FROM ad_group
    """
    conditions = []
    if campaign_id:
        conditions.append(f"campaign.id = {campaign_id}")
    if status:
        conditions.append(f"ad_group.status = '{status.upper()}'")
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    response = googleads_service.search(customer_id=str(customer_id), query=query)
    return [row.ad_group for row in response]

def create_ad_group(client, customer_id, campaign_id, name, status='ENABLED', cpc_bid_micros=None):
    ad_group_service = client.get_service("AdGroupService")
    googleads_service = client.get_service("GoogleAdsService")
    
    op = client.get_type("AdGroupOperation")
    ad_group = op.create
    ad_group.name = name
    ad_group.status = getattr(AdGroupStatusEnum, status.upper())
    ad_group.campaign = googleads_service.campaign_path(customer_id, campaign_id)
    ad_group.type_ = client.enums.AdGroupTypeEnum.SEARCH_STANDARD
    if cpc_bid_micros:
        ad_group.cpc_bid_micros = cpc_bid_micros
    
    response = ad_group_service.mutate_ad_groups(customer_id=str(customer_id), operations=[op])
    return response.results[0].resource_name

def update_ad_group(client, customer_id, ad_group_id, name=None, status=None, cpc_bid_micros=None):
    ad_group_service = client.get_service("AdGroupService")
    googleads_service = client.get_service("GoogleAdsService")
    
    ad_group = client.get_type("AdGroup")
    ad_group.resource_name = googleads_service.ad_group_path(customer_id, ad_group_id)
    
    if name:
        ad_group.name = name
    if status:
        ad_group.status = getattr(AdGroupStatusEnum, status.upper())
    if cpc_bid_micros:
        ad_group.cpc_bid_micros = cpc_bid_micros
    
    op = client.get_type("AdGroupOperation")
    op.update = ad_group
    op.update_mask = client.get_type("FieldMask")
    paths = []
    if name: paths.append("name")
    if status: paths.append("status")
    if cpc_bid_micros: paths.append("cpc_bid_micros")
    client.copy_from(op.update_mask, paths)
    
    response = ad_group_service.mutate_ad_groups(customer_id=str(customer_id), operations=[op])
    return response.results[0].resource_name

# Ad Management Functions (from previous scripts)

def list_ads(client, customer_id, ad_group_id=None, status=None):
    googleads_service = client.get_service("GoogleAdsService")
    query = """
        SELECT 
            ad_group_ad.ad.id,
            ad_group_ad.ad.name,
            ad_group_ad.status,
            ad_group.id,
            ad_group.name,
            campaign.id,
            campaign.name,
            ad_group_ad.ad.responsive_search_ad.headlines,
            ad_group_ad.ad.responsive_search_ad.descriptions,
            ad_group_ad.ad.final_urls
        FROM ad_group_ad
        WHERE ad_group_ad.ad.type = RESPONSIVE_SEARCH_AD
    """
    conditions = []
    if ad_group_id:
        conditions.append(f"ad_group.id = {ad_group_id}")
    if status:
        conditions.append(f"ad_group_ad.status = '{status.upper()}'")
    if conditions:
        query += " AND " + " AND ".join(conditions)
    
    response = googleads_service.search(customer_id=str(customer_id), query=query)
    ads = []
    for row in response:
        ad = row.ad_group_ad.ad
        ads.append({
            'id': ad.id,
            'name': ad.name,
            'status': row.ad_group_ad.status,
            'ad_group_id': row.ad_group.id,
            'campaign_id': row.campaign.id,
            'headlines': [h.text for h in ad.responsive_search_ad.headlines],
            'descriptions': [d.text for d in ad.responsive_search_ad.descriptions],
            'final_urls': ad.final_urls
        })
    return ads

def create_ad(client, customer_id, ad_group_id, headlines, descriptions, final_urls, status='ENABLED'):
    ad_group_ad_service = client.get_service("AdGroupAdService")
    googleads_service = client.get_service("GoogleAdsService")
    
    op = client.get_type("AdGroupAdOperation")
    ad_group_ad = op.create
    ad_group_ad.ad_group = googleads_service.ad_group_path(customer_id, ad_group_id)
    ad_group_ad.status = getattr(AdGroupAdStatusEnum, status.upper())
    
    rsa = ad_group_ad.ad.responsive_search_ad
    for text in headlines:
        headline = client.get_type("AdTextAsset")
        headline.text = text
        rsa.headlines.append(headline)
    for text in descriptions:
        desc = client.get_type("AdTextAsset")
        desc.text = text
        rsa.descriptions.append(desc)
    ad_group_ad.ad.final_urls.extend(final_urls)
    
    response = ad_group_ad_service.mutate_ad_group_ads(customer_id=str(customer_id), operations=[op])
    return response.results[0].resource_name

def update_ad(client, customer_id, ad_group_id, ad_id, headlines=None, descriptions=None, final_urls=None, status=None):
    ad_group_ad_service = client.get_service("AdGroupAdService")
    googleads_service = client.get_service("GoogleAdsService")
    
    ad_group_ad = client.get_type("AdGroupAd")
    ad_group_ad.resource_name = googleads_service.ad_group_ad_path(customer_id, ad_group_id, ad_id)
    
    if status:
        ad_group_ad.status = getattr(AdGroupAdStatusEnum, status.upper())
    
    rsa = ad_group_ad.ad.responsive_search_ad
    if headlines:
        rsa.headlines.clear()
        for text in headlines:
            headline = client.get_type("AdTextAsset")
            headline.text = text
            rsa.headlines.append(headline)
    if descriptions:
        rsa.descriptions.clear()
        for text in descriptions:
            desc = client.get_type("AdTextAsset")
            desc.text = text
            rsa.descriptions.append(desc)
    if final_urls:
        ad_group_ad.ad.final_urls[:] = final_urls
    
    op = client.get_type("AdGroupAdOperation")
    op.update = ad_group_ad
    op.update_mask = client.get_type("FieldMask")
    paths = []
    if headlines: paths.append("ad.responsive_search_ad.headlines")
    if descriptions: paths.append("ad.responsive_search_ad.descriptions")
    if final_urls: paths.append("ad.final_urls")
    if status: paths.append("status")
    client.copy_from(op.update_mask, paths)
    
    response = ad_group_ad_service.mutate_ad_group_ads(customer_id=str(customer_id), operations=[op])
    return response.results[0].resource_name

# Output Helpers

def print_items(items, entity_type):
    if not items:
        print(f"No {entity_type} found.")
        return
    for item in items:
        print(f"{entity_type.upper()} ID: {item.get('id', item.id)}")
        print(f"Name: {item.get('name', item.name)}")
        print(f"Status: {item.get('status', item.status).name}")
        if hasattr(item, 'advertising_channel_type'):
            print(f"Type: {item.advertising_channel_type.name}")
        if 'campaign_id' in item:
            print(f"Campaign ID: {item['campaign_id']}")
        if 'headlines' in item:
            print("Headlines:", ", ".join(item['headlines']))
        if 'descriptions' in item:
            print("Descriptions:", ", ".join(item['descriptions']))
        if 'final_urls' in item:
            print("Final URLs:", ", ".join(item['final_urls']))
        print("---")

def save_to_csv(items, filename):
    if not items:
        return
    os.makedirs(REPORTS_DIR, exist_ok=True)
    path = os.path.join(REPORTS_DIR, filename)
    with open(path, 'w', newline='') as f:
        writer = csv.writer(f)
        # Write headers and rows based on item type
        if isinstance(items[0], dict):
            headers = items[0].keys()
            writer.writerow(headers)
            for item in items:
                writer.writerow(item.values())
        else:
            # For protobuf objects, extract fields
            headers = ['id', 'name', 'status']
            writer.writerow(headers)
            for item in items:
                writer.writerow([item.id, item.name, item.status.name])
    print(f"Report saved to {path}")

# Main CLI Setup

def main():
    parser = argparse.ArgumentParser(description="Google Ads Manager")
    subparsers = parser.add_subparsers(dest='entity', required=True)
    
    # Campaign parsers
    campaign_parser = subparsers.add_parser('campaign')
    campaign_sub = campaign_parser.add_subparsers(dest='action', required=True)
    
    camp_list = campaign_sub.add_parser('list')
    camp_list.add_argument('--customer-id', required=True)
    camp_list.add_argument('--status')
    camp_list.add_argument('--csv', action='store_true')
    
    camp_create = campaign_sub.add_parser('create')
    camp_create.add_argument('--customer-id', required=True)
    camp_create.add_argument('--name', required=True)
    camp_create.add_argument('--budget', type=int, required=True)
    camp_create.add_argument('--channel-type', default='SEARCH')
    camp_create.add_argument('--status', default='PAUSED')
    camp_create.add_argument('--start-date')
    camp_create.add_argument('--end-date')
    
    camp_update = campaign_sub.add_parser('update')
    camp_update.add_argument('--customer-id', required=True)
    camp_update.add_argument('--campaign-id', required=True)
    camp_update.add_argument('--name')
    camp_update.add_argument('--status')
    camp_update.add_argument('--budget')
    
    # AdGroup parsers
    adgroup_parser = subparsers.add_parser('adgroup')
    adgroup_sub = adgroup_parser.add_subparsers(dest='action', required=True)
    
    ag_list = adgroup_sub.add_parser('list')
    ag_list.add_argument('--customer-id', required=True)
    ag_list.add_argument('--campaign-id')
    ag_list.add_argument('--status')
    ag_list.add_argument('--csv', action='store_true')
    
    ag_create = adgroup_sub.add_parser('create')
    ag_create.add_argument('--customer-id', required=True)
    ag_create.add_argument('--campaign-id', required=True)
    ag_create.add_argument('--name', required=True)
    ag_create.add_argument('--status', default='ENABLED')
    ag_create.add_argument('--cpc-bid', type=int)
    
    ag_update = adgroup_sub.add_parser('update')
    ag_update.add_argument('--customer-id', required=True)
    ag_update.add_argument('--ad-group-id', required=True)
    ag_update.add_argument('--name')
    ag_update.add_argument('--status')
    ag_update.add_argument('--cpc-bid', type=int)
    
    # Ad parsers
    ad_parser = subparsers.add_parser('ad')
    ad_sub = ad_parser.add_subparsers(dest='action', required=True)
    
    ad_list = ad_sub.add_parser('list')
    ad_list.add_argument('--customer-id', required=True)
    ad_list.add_argument('--ad-group-id')
    ad_list.add_argument('--status')
    ad_list.add_argument('--csv', action='store_true')
    
    ad_create = ad_sub.add_parser('create')
    ad_create.add_argument('--customer-id', required=True)
    ad_create.add_argument('--ad-group-id', required=True)
    ad_create.add_argument('--headlines', nargs='+', required=True)
    ad_create.add_argument('--descriptions', nargs='+', required=True)
    ad_create.add_argument('--final-urls', nargs='+', required=True)
    ad_create.add_argument('--status', default='ENABLED')
    
    ad_update = ad_sub.add_parser('update')
    ad_update.add_argument('--customer-id', required=True)
    ad_update.add_argument('--ad-group-id', required=True)
    ad_update.add_argument('--ad-id', required=True)
    ad_update.add_argument('--headlines', nargs='+')
    ad_update.add_argument('--descriptions', nargs='+')
    ad_update.add_argument('--final-urls', nargs='+')
    ad_update.add_argument('--status')
    
    args = parser.parse_args()
    
    client = setup_client()
    
    try:
        if args.entity == 'campaign':
            if args.action == 'list':
                items = list_campaigns(client, args.customer_id, args.status)
                print_items(items, 'campaign')
                if args.csv:
                    save_to_csv(items, f"campaigns_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
            elif args.action == 'create':
                resource = create_campaign(client, args.customer_id, args.name, args.budget, 
                                         args.channel_type, args.status, args.start_date, args.end_date)
                print(f"Created campaign: {resource}")
            elif args.action == 'update':
                resource = update_campaign(client, args.customer_id, args.campaign_id, 
                                         args.name, args.status, args.budget)
                print(f"Updated campaign: {resource}")
        
        elif args.entity == 'adgroup':
            if args.action == 'list':
                items = list_ad_groups(client, args.customer_id, args.campaign_id, args.status)
                print_items(items, 'adgroup')
                if args.csv:
                    save_to_csv(items, f"adgroups_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
            elif args.action == 'create':
                resource = create_ad_group(client, args.customer_id, args.campaign_id, 
                                         args.name, args.status, args.cpc_bid)
                print(f"Created ad group: {resource}")
            elif args.action == 'update':
                resource = update_ad_group(client, args.customer_id, args.ad_group_id, 
                                         args.name, args.status, args.cpc_bid)
                print(f"Updated ad group: {resource}")
        
        elif args.entity == 'ad':
            if args.action == 'list':
                items = list_ads(client, args.customer_id, args.ad_group_id, args.status)
                print_items(items, 'ad')
                if args.csv:
                    save_to_csv(items, f"ads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
            elif args.action == 'create':
                resource = create_ad(client, args.customer_id, args.ad_group_id, 
                                   args.headlines, args.descriptions, args.final_urls, args.status)
                print(f"Created ad: {resource}")
            elif args.action == 'update':
                resource = update_ad(client, args.customer_id, args.ad_group_id, args.ad_id,
                                   args.headlines, args.descriptions, args.final_urls, args.status)
                print(f"Updated ad: {resource}")
    
    except GoogleAdsException as ex:
        print(f"Request failed with status {ex.error.code().name}: {ex.failure}")
        for error in ex.failure.errors:
            print(f"Error: {error.message}")
            if error.location:
                for field in error.location.field_path_elements:
                    print(f" - Field: {field.field_name}")

if __name__ == "__main__":
    main()
