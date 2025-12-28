"""
Google Ads Management Script
View, duplicate, and create ads in Google Ads campaigns

DDEV Usage:
    ddev exec python3 scripts/manage_google_ads.py

Features:
    - List all campaigns and ad groups
    - View all ads in a specific ad group
    - Duplicate existing ads
    - Create new responsive search ads
    - Interactive menu-driven interface
"""

import os
import sys
from datetime import datetime
import json

# Add the parent directory to sys.path to import src modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.config import REPORTS_DIR, get_google_ads_client, GOOGLE_ADS_CUSTOMER_ID

def list_campaigns(client, customer_id):
    """List all active campaigns"""
    
    googleads_service = client.get_service("GoogleAdsService")
    
    query = """
        SELECT
            campaign.id,
            campaign.name,
            campaign.status,
            campaign.advertising_channel_type
        FROM campaign
        WHERE campaign.status = 'ENABLED'
        ORDER BY campaign.name
    """
    
    request = client.get_type("SearchGoogleAdsRequest")
    request.customer_id = customer_id
    request.query = query
    
    response = googleads_service.search(request=request)
    
    campaigns = []
    for row in response:
        campaigns.append({
            'id': row.campaign.id,
            'name': row.campaign.name,
            'status': row.campaign.status.name,
            'type': row.campaign.advertising_channel_type.name
        })
    
    return campaigns

def list_ad_groups(client, customer_id, campaign_id):
    """List ad groups in a specific campaign"""
    
    googleads_service = client.get_service("GoogleAdsService")
    
    query = f"""
        SELECT
            ad_group.id,
            ad_group.name,
            ad_group.status,
            campaign.id,
            campaign.name
        FROM ad_group
        WHERE campaign.id = {campaign_id}
        AND ad_group.status = 'ENABLED'
        ORDER BY ad_group.name
    """
    
    request = client.get_type("SearchGoogleAdsRequest")
    request.customer_id = customer_id
    request.query = query
    
    response = googleads_service.search(request=request)
    
    ad_groups = []
    for row in response:
        ad_groups.append({
            'id': row.ad_group.id,
            'name': row.ad_group.name,
            'status': row.ad_group.status.name,
            'campaign_id': row.campaign.id,
            'campaign_name': row.campaign.name
        })
    
    return ad_groups

def list_ads_in_ad_group(client, customer_id, ad_group_id):
    """List all ads in a specific ad group with detailed information"""
    
    googleads_service = client.get_service("GoogleAdsService")
    
    query = f"""
        SELECT
            ad_group_ad.ad.id,
            ad_group_ad.ad.name,
            ad_group_ad.status,
            ad_group_ad.ad.type,
            ad_group_ad.ad.responsive_search_ad.headlines,
            ad_group_ad.ad.responsive_search_ad.descriptions,
            ad_group_ad.ad.final_urls,
            ad_group_ad.ad.final_mobile_urls,
            ad_group_ad.policy_summary.approval_status,
            ad_group.id,
            ad_group.name,
            campaign.id,
            campaign.name
        FROM ad_group_ad
        WHERE ad_group.id = {ad_group_id}
        ORDER BY ad_group_ad.ad.id
    """
    
    request = client.get_type("SearchGoogleAdsRequest")
    request.customer_id = customer_id
    request.query = query
    
    response = googleads_service.search(request=request)
    
    ads = []
    for row in response:
        ad_info = {
            'id': row.ad_group_ad.ad.id,
            'name': row.ad_group_ad.ad.name if row.ad_group_ad.ad.name else f"Ad {row.ad_group_ad.ad.id}",
            'status': row.ad_group_ad.status.name,
            'type': row.ad_group_ad.ad.type_.name,
            'approval_status': row.ad_group_ad.policy_summary.approval_status.name,
            'ad_group_id': row.ad_group.id,
            'ad_group_name': row.ad_group.name,
            'campaign_id': row.campaign.id,
            'campaign_name': row.campaign.name,
            'headlines': [],
            'descriptions': [],
            'final_urls': list(row.ad_group_ad.ad.final_urls),
            'final_mobile_urls': list(row.ad_group_ad.ad.final_mobile_urls) if row.ad_group_ad.ad.final_mobile_urls else []
        }
        
        # Extract headlines for responsive search ads
        if row.ad_group_ad.ad.type_.name == 'RESPONSIVE_SEARCH_AD':
            for headline in row.ad_group_ad.ad.responsive_search_ad.headlines:
                ad_info['headlines'].append({
                    'text': headline.text,
                    'pinned_field': headline.pinned_field.name if headline.pinned_field else None
                })
            
            for description in row.ad_group_ad.ad.responsive_search_ad.descriptions:
                ad_info['descriptions'].append({
                    'text': description.text,
                    'pinned_field': description.pinned_field.name if description.pinned_field else None
                })
        
        ads.append(ad_info)
    
    return ads

def display_ad_details(ad):
    """Display detailed information about an ad"""
    
    print(f"\n{'='*80}")
    print(f"Ad ID: {ad['id']}")
    print(f"Ad Name: {ad['name']}")
    print(f"Status: {ad['status']}")
    print(f"Type: {ad['type']}")
    print(f"Approval Status: {ad['approval_status']}")
    print(f"Campaign: {ad['campaign_name']} (ID: {ad['campaign_id']})")
    print(f"Ad Group: {ad['ad_group_name']} (ID: {ad['ad_group_id']})")
    
    if ad['type'] == 'RESPONSIVE_SEARCH_AD':
        print(f"\n📝 Headlines ({len(ad['headlines'])}):")
        for i, headline in enumerate(ad['headlines'], 1):
            pinned = f" [Pinned: {headline['pinned_field']}]" if headline['pinned_field'] and headline['pinned_field'] != 'UNSPECIFIED' else ""
            print(f"  {i}. {headline['text']}{pinned}")
        
        print(f"\n📝 Descriptions ({len(ad['descriptions'])}):")
        for i, desc in enumerate(ad['descriptions'], 1):
            pinned = f" [Pinned: {desc['pinned_field']}]" if desc['pinned_field'] and desc['pinned_field'] != 'UNSPECIFIED' else ""
            print(f"  {i}. {desc['text']}{pinned}")
    
    print(f"\n🔗 Final URLs:")
    for url in ad['final_urls']:
        print(f"  • {url}")
    
    if ad['final_mobile_urls']:
        print(f"\n📱 Mobile URLs:")
        for url in ad['final_mobile_urls']:
            print(f"  • {url}")
    
    print(f"{'='*80}")

def create_responsive_search_ad(client, customer_id, ad_group_id, headlines, descriptions, final_urls, ad_name=None):
    """Create a new responsive search ad"""
    
    ad_group_ad_service = client.get_service("AdGroupAdService")
    googleads_service = client.get_service("GoogleAdsService")
    
    operation = client.get_type("AdGroupAdOperation")
    ad_group_ad = operation.create
    
    # Set the ad group
    ad_group_ad.ad_group = googleads_service.ad_group_path(customer_id, ad_group_id)
    
    # Set status to enabled
    ad_group_ad.status = client.enums.AdGroupAdStatusEnum.ENABLED
    
    # Set ad name if provided
    if ad_name:
        ad_group_ad.ad.name = ad_name
    
    # Create responsive search ad
    responsive_search_ad = ad_group_ad.ad.responsive_search_ad
    
    # Add headlines
    for headline_text in headlines:
        headline = client.get_type("AdTextAsset")
        headline.text = headline_text
        responsive_search_ad.headlines.append(headline)
    
    # Add descriptions
    for desc_text in descriptions:
        description = client.get_type("AdTextAsset")
        description.text = desc_text
        responsive_search_ad.descriptions.append(description)
    
    # Set final URLs
    ad_group_ad.ad.final_urls.extend(final_urls)
    
    # Execute the operation
    response = ad_group_ad_service.mutate_ad_group_ads(
        customer_id=customer_id,
        operations=[operation]
    )
    
    return response.results[0].resource_name

def duplicate_ad(client, customer_id, source_ad, target_ad_group_id=None, modifications=None):
    """Duplicate an existing ad, optionally with modifications"""
    
    # Use source ad group if target not specified
    if not target_ad_group_id:
        target_ad_group_id = source_ad['ad_group_id']
    
    # Extract headlines and descriptions
    headlines = [h['text'] for h in source_ad['headlines']]
    descriptions = [d['text'] for d in source_ad['descriptions']]
    final_urls = source_ad['final_urls']
    
    # Apply modifications if provided
    if modifications:
        if 'headlines' in modifications:
            headlines = modifications['headlines']
        if 'descriptions' in modifications:
            descriptions = modifications['descriptions']
        if 'final_urls' in modifications:
            final_urls = modifications['final_urls']
    
    # Create new ad name
    ad_name = f"Copy of {source_ad['name']}"
    
    # Create the ad
    return create_responsive_search_ad(
        client=client,
        customer_id=customer_id,
        ad_group_id=target_ad_group_id,
        headlines=headlines,
        descriptions=descriptions,
        final_urls=final_urls,
        ad_name=ad_name
    )

def save_ad_to_file(ad, filename=None):
    """Save ad details to a JSON file for reference"""
    
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(REPORTS_DIR, f"ad_details_{ad['id']}_{timestamp}.json")
    
    with open(filename, 'w') as f:
        json.dump(ad, f, indent=2)
    
    return filename

def interactive_menu():
    """Interactive menu for managing Google Ads"""
    
    print("\n" + "="*80)
    print("🎯 GOOGLE ADS MANAGEMENT TOOL")
    print("="*80)
    
    # Get customer ID from environment
    customer_id = GOOGLE_ADS_CUSTOMER_ID
    
    if not customer_id:
        print("\n❌ Error: GOOGLE_ADS_CUSTOMER_ID not found in .env file")
        print("Please add GOOGLE_ADS_CUSTOMER_ID to your .env file and try again.")
        return
    
    # Remove dashes if present
    customer_id = customer_id.replace("-", "")
    print(f"\n✅ Using Customer ID: {customer_id}")
    
    try:
        client = get_google_ads_client()
        
        while True:
            print("\n" + "-"*80)
            print("📋 MAIN MENU")
            print("-"*80)
            print("1. List all campaigns")
            print("2. List ad groups in a campaign")
            print("3. View ads in an ad group")
            print("4. View detailed ad information")
            print("5. Duplicate an ad")
            print("6. Create a new ad")
            print("7. Save ad details to file")
            print("0. Exit")
            
            choice = input("\nEnter your choice: ").strip()
            
            if choice == "0":
                print("\n👋 Goodbye!")
                break
            
            elif choice == "1":
                # List campaigns
                print("\n📊 Fetching campaigns...")
                campaigns = list_campaigns(client, customer_id)
                
                if not campaigns:
                    print("❌ No active campaigns found.")
                    continue
                
                print(f"\n✅ Found {len(campaigns)} active campaigns:")
                print(f"{'ID':<15} {'Name':<40} {'Type':<20}")
                print("-"*80)
                for campaign in campaigns:
                    print(f"{campaign['id']:<15} {campaign['name']:<40} {campaign['type']:<20}")
            
            elif choice == "2":
                # List ad groups
                campaign_id = input("\nEnter Campaign ID: ").strip()
                print(f"\n📊 Fetching ad groups for campaign {campaign_id}...")
                
                ad_groups = list_ad_groups(client, customer_id, campaign_id)
                
                if not ad_groups:
                    print("❌ No active ad groups found in this campaign.")
                    continue
                
                print(f"\n✅ Found {len(ad_groups)} active ad groups:")
                print(f"{'ID':<15} {'Name':<40} {'Status':<15}")
                print("-"*80)
                for ag in ad_groups:
                    print(f"{ag['id']:<15} {ag['name']:<40} {ag['status']:<15}")
            
            elif choice == "3":
                # View ads in ad group
                ad_group_id = input("\nEnter Ad Group ID: ").strip()
                print(f"\n📊 Fetching ads in ad group {ad_group_id}...")
                
                ads = list_ads_in_ad_group(client, customer_id, ad_group_id)
                
                if not ads:
                    print("❌ No ads found in this ad group.")
                    continue
                
                print(f"\n✅ Found {len(ads)} ads:")
                print(f"{'ID':<15} {'Name':<30} {'Type':<25} {'Status':<15} {'Approval':<15}")
                print("-"*100)
                for ad in ads:
                    print(f"{ad['id']:<15} {ad['name'][:29]:<30} {ad['type']:<25} {ad['status']:<15} {ad['approval_status']:<15}")
            
            elif choice == "4":
                # View detailed ad information
                ad_group_id = input("\nEnter Ad Group ID: ").strip()
                ad_id = input("Enter Ad ID: ").strip()
                
                print(f"\n📊 Fetching ad details...")
                ads = list_ads_in_ad_group(client, customer_id, ad_group_id)
                
                selected_ad = None
                for ad in ads:
                    if str(ad['id']) == ad_id:
                        selected_ad = ad
                        break
                
                if not selected_ad:
                    print("❌ Ad not found in this ad group.")
                    continue
                
                display_ad_details(selected_ad)
            
            elif choice == "5":
                # Duplicate an ad
                ad_group_id = input("\nEnter Source Ad Group ID: ").strip()
                ad_id = input("Enter Ad ID to duplicate: ").strip()
                
                print(f"\n📊 Fetching ad details...")
                ads = list_ads_in_ad_group(client, customer_id, ad_group_id)
                
                source_ad = None
                for ad in ads:
                    if str(ad['id']) == ad_id:
                        source_ad = ad
                        break
                
                if not source_ad:
                    print("❌ Ad not found.")
                    continue
                
                display_ad_details(source_ad)
                
                # Ask if they want to modify
                modify = input("\nDo you want to modify the ad before duplicating? (y/n): ").strip().lower()
                modifications = None
                
                if modify == 'y':
                    print("\nLeave blank to keep original values.")
                    
                    # Modify headlines
                    print(f"\nCurrent headlines ({len(source_ad['headlines'])}):")
                    for i, h in enumerate(source_ad['headlines'], 1):
                        print(f"  {i}. {h['text']}")
                    
                    modify_headlines = input("\nModify headlines? (y/n): ").strip().lower()
                    if modify_headlines == 'y':
                        new_headlines = []
                        print("Enter new headlines (press Enter with empty line to finish, max 15):")
                        while len(new_headlines) < 15:
                            headline = input(f"Headline {len(new_headlines) + 1}: ").strip()
                            if not headline:
                                break
                            if len(headline) <= 30:
                                new_headlines.append(headline)
                            else:
                                print(f"  ⚠️  Headline too long ({len(headline)} chars, max 30)")
                        
                        if new_headlines:
                            if not modifications:
                                modifications = {}
                            modifications['headlines'] = new_headlines
                    
                    # Modify descriptions
                    print(f"\nCurrent descriptions ({len(source_ad['descriptions'])}):")
                    for i, d in enumerate(source_ad['descriptions'], 1):
                        print(f"  {i}. {d['text']}")
                    
                    modify_descriptions = input("\nModify descriptions? (y/n): ").strip().lower()
                    if modify_descriptions == 'y':
                        new_descriptions = []
                        print("Enter new descriptions (press Enter with empty line to finish, max 4):")
                        while len(new_descriptions) < 4:
                            desc = input(f"Description {len(new_descriptions) + 1}: ").strip()
                            if not desc:
                                break
                            if len(desc) <= 90:
                                new_descriptions.append(desc)
                            else:
                                print(f"  ⚠️  Description too long ({len(desc)} chars, max 90)")
                        
                        if new_descriptions:
                            if not modifications:
                                modifications = {}
                            modifications['descriptions'] = new_descriptions
                
                # Ask for target ad group
                same_group = input(f"\nDuplicate in same ad group ({source_ad['ad_group_name']})? (y/n): ").strip().lower()
                target_ad_group_id = None
                if same_group != 'y':
                    target_ad_group_id = input("Enter target Ad Group ID: ").strip()
                
                print("\n🚀 Creating duplicate ad...")
                try:
                    new_ad_resource = duplicate_ad(
                        client=client,
                        customer_id=customer_id,
                        source_ad=source_ad,
                        target_ad_group_id=target_ad_group_id,
                        modifications=modifications
                    )
                    print(f"✅ Ad duplicated successfully!")
                    print(f"Resource name: {new_ad_resource}")
                except Exception as e:
                    print(f"❌ Error duplicating ad: {e}")
            
            elif choice == "6":
                # Create new ad
                ad_group_id = input("\nEnter Ad Group ID: ").strip()
                ad_name = input("Enter Ad Name (optional): ").strip() or None
                
                print("\n📝 Enter ad headlines (3-15 required, max 30 characters each):")
                headlines = []
                while len(headlines) < 15:
                    headline = input(f"Headline {len(headlines) + 1}: ").strip()
                    if not headline and len(headlines) >= 3:
                        break
                    if headline:
                        if len(headline) <= 30:
                            headlines.append(headline)
                        else:
                            print(f"  ⚠️  Headline too long ({len(headline)} chars, max 30)")
                
                if len(headlines) < 3:
                    print("❌ At least 3 headlines required.")
                    continue
                
                print("\n📝 Enter ad descriptions (2-4 required, max 90 characters each):")
                descriptions = []
                while len(descriptions) < 4:
                    desc = input(f"Description {len(descriptions) + 1}: ").strip()
                    if not desc and len(descriptions) >= 2:
                        break
                    if desc:
                        if len(desc) <= 90:
                            descriptions.append(desc)
                        else:
                            print(f"  ⚠️  Description too long ({len(desc)} chars, max 90)")
                
                if len(descriptions) < 2:
                    print("❌ At least 2 descriptions required.")
                    continue
                
                print("\n🔗 Enter final URLs (at least 1 required):")
                final_urls = []
                while True:
                    url = input(f"URL {len(final_urls) + 1} (or press Enter to finish): ").strip()
                    if not url and len(final_urls) >= 1:
                        break
                    if url:
                        final_urls.append(url)
                
                if not final_urls:
                    print("❌ At least 1 final URL required.")
                    continue
                
                print("\n🚀 Creating new ad...")
                print(f"Headlines: {len(headlines)}")
                print(f"Descriptions: {len(descriptions)}")
                print(f"URLs: {len(final_urls)}")
                
                confirm = input("\nCreate this ad? (y/n): ").strip().lower()
                if confirm == 'y':
                    try:
                        new_ad_resource = create_responsive_search_ad(
                            client=client,
                            customer_id=customer_id,
                            ad_group_id=ad_group_id,
                            headlines=headlines,
                            descriptions=descriptions,
                            final_urls=final_urls,
                            ad_name=ad_name
                        )
                        print(f"✅ Ad created successfully!")
                        print(f"Resource name: {new_ad_resource}")
                        
                        # Save details
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        report_file = os.path.join(REPORTS_DIR, f"ad_created_{timestamp}.json")
                        with open(report_file, 'w') as f:
                            json.dump({
                                'created_at': datetime.now().isoformat(),
                                'customer_id': customer_id,
                                'ad_group_id': ad_group_id,
                                'ad_name': ad_name,
                                'headlines': headlines,
                                'descriptions': descriptions,
                                'final_urls': final_urls,
                                'resource_name': new_ad_resource
                            }, f, indent=2)
                        print(f"📄 Details saved to: {report_file}")
                    except Exception as e:
                        print(f"❌ Error creating ad: {e}")
            
            elif choice == "7":
                # Save ad details
                ad_group_id = input("\nEnter Ad Group ID: ").strip()
                ad_id = input("Enter Ad ID: ").strip()
                
                print(f"\n📊 Fetching ad details...")
                ads = list_ads_in_ad_group(client, customer_id, ad_group_id)
                
                selected_ad = None
                for ad in ads:
                    if str(ad['id']) == ad_id:
                        selected_ad = ad
                        break
                
                if not selected_ad:
                    print("❌ Ad not found.")
                    continue
                
                filename = save_ad_to_file(selected_ad)
                print(f"✅ Ad details saved to: {filename}")
            
            else:
                print("❌ Invalid choice. Please try again.")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    interactive_menu()
