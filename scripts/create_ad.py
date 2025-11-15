"""
Create New Ads in Google Ads Campaigns Script
Creates responsive search ads in existing ad groups
"""

import os
import sys
import argparse
from datetime import datetime

# Add the parent directory to sys.path to import src modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.config import REPORTS_DIR, get_google_ads_client

def create_responsive_search_ad(client, customer_id, ad_group_id, headlines, descriptions, final_urls):
    """Create a responsive search ad in the specified ad group"""

    # Get the Google Ads service
    ad_group_ad_service = client.get_service("AdGroupAdService")
    googleads_service = client.get_service("GoogleAdsService")

    # Create the ad group ad operation
    operation = client.get_type("AdGroupAdOperation")
    ad_group_ad = operation.create

    # Set the ad group
    ad_group_ad.ad_group = googleads_service.ad_group_path(customer_id, ad_group_id)

    # Set status to enabled
    ad_group_ad.status = client.enums.AdGroupAdStatusEnum.ENABLED

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

def list_ad_groups(client, customer_id, campaign_id=None):
    """List ad groups in the account or specific campaign"""

    googleads_service = client.get_service("GoogleAdsService")

    query = """
        SELECT
            ad_group.id,
            ad_group.name,
            campaign.id,
            campaign.name
        FROM ad_group
        WHERE ad_group.status = 'ENABLED'
    """

    if campaign_id:
        query += f" AND campaign.id = {campaign_id}"

    request = client.get_type("SearchGoogleAdsRequest")
    request.customer_id = customer_id
    request.query = query

    response = googleads_service.search(request=request)

    ad_groups = []
    for row in response:
        ad_groups.append({
            'id': row.ad_group.id,
            'name': row.ad_group.name,
            'campaign_id': row.campaign.id,
            'campaign_name': row.campaign.name
        })

    return ad_groups

def list_campaigns(client, customer_id):
    """List active campaigns"""

    googleads_service = client.get_service("GoogleAdsService")

    query = """
        SELECT
            campaign.id,
            campaign.name,
            campaign.status
        FROM campaign
        WHERE campaign.status = 'ENABLED'
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
            'status': row.campaign.status
        })

    return campaigns

def main():
    parser = argparse.ArgumentParser(description="Create new ads in Google Ads campaigns")
    parser.add_argument("--customer-id", required=True, help="Google Ads customer ID (without dashes)")
    parser.add_argument("--ad-group-id", help="Ad group ID to create ad in")
    parser.add_argument("--campaign-id", help="Campaign ID to list ad groups from")
    parser.add_argument("--headlines", nargs='+', required=True, help="Ad headlines (up to 15)")
    parser.add_argument("--descriptions", nargs='+', required=True, help="Ad descriptions (up to 4)")
    parser.add_argument("--final-urls", nargs='+', required=True, help="Final URLs for the ad")

    args = parser.parse_args()

    try:
        # Initialize client
        client = get_google_ads_client()

        print("🎯 Google Ads Ad Creation Tool")
        print("=" * 50)

        # If no ad group specified, list campaigns and ad groups
        if not args.ad_group_id:
            if not args.campaign_id:
                print("\n📋 Available Campaigns:")
                campaigns = list_campaigns(client, args.customer_id)
                if not campaigns:
                    print("❌ No active campaigns found.")
                    return

                for campaign in campaigns:
                    print(f"  {campaign['id']}: {campaign['name']}")

                campaign_id = input("\nEnter campaign ID: ").strip()
            else:
                campaign_id = args.campaign_id

            print(f"\n📋 Ad Groups in Campaign {campaign_id}:")
            ad_groups = list_ad_groups(client, args.customer_id, campaign_id)
            if not ad_groups:
                print("❌ No ad groups found in this campaign.")
                return

            for ag in ad_groups:
                print(f"  {ag['id']}: {ag['name']}")

            ad_group_id = input("\nEnter ad group ID: ").strip()
        else:
            ad_group_id = args.ad_group_id

        # Validate inputs
        if len(args.headlines) > 15:
            print("❌ Too many headlines. Maximum 15 allowed.")
            return

        if len(args.descriptions) > 4:
            print("❌ Too many descriptions. Maximum 4 allowed.")
            return

        print(f"\n🚀 Creating responsive search ad in ad group {ad_group_id}")
        print(f"Headlines: {args.headlines}")
        print(f"Descriptions: {args.descriptions}")
        print(f"Final URLs: {args.final_urls}")

        # Create the ad
        ad_resource_name = create_responsive_search_ad(
            client=client,
            customer_id=args.customer_id,
            ad_group_id=ad_group_id,
            headlines=args.headlines,
            descriptions=args.descriptions,
            final_urls=args.final_urls
        )

        print(f"\n✅ Ad created successfully!")
        print(f"Resource name: {ad_resource_name}")

        # Save to reports
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        report_file = os.path.join(REPORTS_DIR, f"ad_creation_{timestamp}.txt")

        with open(report_file, 'w') as f:
            f.write(f"Ad created at: {datetime.now()}\n")
            f.write(f"Customer ID: {args.customer_id}\n")
            f.write(f"Ad Group ID: {ad_group_id}\n")
            f.write(f"Headlines: {', '.join(args.headlines)}\n")
            f.write(f"Descriptions: {', '.join(args.descriptions)}\n")
            f.write(f"Final URLs: {', '.join(args.final_urls)}\n")
            f.write(f"Ad Resource Name: {ad_resource_name}\n")

        print(f"📄 Report saved to: {report_file}")

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()