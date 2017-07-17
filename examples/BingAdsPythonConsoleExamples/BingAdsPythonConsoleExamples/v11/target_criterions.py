from auth_helper import *
from output_helper import *

# You must provide credentials in auth_helper.py.

def get_example_campaign_ids(authorization_data):

    campaigns=campaign_service.factory.create('ArrayOfCampaign')
    campaign=set_elements_to_none(campaign_service.factory.create('Campaign'))
    campaign.CampaignType=['SearchAndContent']
    campaign.Name="Women's Shoes " + strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime())
    campaign.Description='Red shoes line.'
    campaign.DailyBudget=50
    campaign.BudgetType='DailyBudgetStandard'
    campaign.TimeZone='PacificTimeUSCanadaTijuana'
    campaigns.Campaign.append(campaign)

    ad_groups=campaign_service.factory.create('ArrayOfAdGroup')

    for index in range(3):
        ad_group=set_elements_to_none(campaign_service.factory.create('AdGroup'))
        ad_group.Name="Women's Shoe Sale " + str(index)
        ad_group.AdDistribution=['Search']
        search_bid=campaign_service.factory.create('Bid')
        search_bid.Amount=0.09
        ad_group.SearchBid=search_bid
        ad_group.Language='English'
        ad_groups.AdGroup.append(ad_group)

    # Add the campaigns and ad groups

    add_campaigns_response=campaign_service.AddCampaigns(
        AccountId=authorization_data.account_id,
        Campaigns=campaigns
    )
    campaign_ids={
        'long': add_campaigns_response.CampaignIds['long'] if add_campaigns_response.CampaignIds['long'] else None
    }
    output_status_message('Campaign Ids:')
    output_ids(campaign_ids)
    if hasattr(add_campaigns_response.PartialErrors, 'BatchError'):
        output_partial_errors(add_campaigns_response.PartialErrors)
        
    add_ad_groups_response=campaign_service.AddAdGroups(
        CampaignId=campaign_ids['long'][0],
        AdGroups=ad_groups
    )
    ad_group_ids={
        'long': add_ad_groups_response.AdGroupIds['long'] if add_ad_groups_response.AdGroupIds['long'] else None
    }
    output_status_message("Ad Group Ids:")
    output_ids(ad_group_ids)
    if hasattr(add_ad_groups_response.PartialErrors, 'BatchError'):
        output_partial_errors(add_ad_groups_response.PartialErrors)

    # This example uses the deprecated version 10 shared target library in order to later demonstrate
    # the inline migration from shared target criterions to unshared target criterions.
    # The shared target ID is output within the share_deprecated_targets method.
    # We won't do anything further with it in this example.

    shared_target_id = share_deprecated_targets(authorization_data, ad_group_ids)

    return campaign_ids

# Shares a target with multiple new ad groups. This helper function is used to setup
# criterion migration scenarios.
# 
# This is an example of a deprecated scenario. In Bing Ads API version 11 you can no longer use 
# the AddTargetsToLibrary, SetTargetToCampaign, or SetTargetToAdGroup operations. Instead you will 
# be required to use criterions. Support for targets will end no later than the sunset 
# of Bing Ads API version 10. 
def share_deprecated_targets(authorization_data, ad_group_ids):
    
    shared_targets=campaign_service_v10.factory.create('ArrayOfTarget')
    shared_target=set_elements_to_none(campaign_service_v10.factory.create('Target'))
    shared_target.Name = "My Target"
    device_os_target=campaign_service_v10.factory.create('DeviceOSTarget')
    device_os_target_bids=campaign_service_v10.factory.create('ArrayOfDeviceOSTargetBid')
    device_os_target_bid=campaign_service_v10.factory.create('DeviceOSTargetBid')
    device_os_target_bid.BidAdjustment = 20
    device_os_target_bid.DeviceName='Computers'
    device_os_target_bids.DeviceOSTargetBid.append(device_os_target_bid)
    device_os_target.Bids=device_os_target_bids
    shared_target.DeviceOS=device_os_target
    shared_targets.Target.append(shared_target)
    
    shared_target_id=campaign_service_v10.AddTargetsToLibrary(Targets=shared_targets)['long'][0]
    output_status_message("Added Target Id: {0}\n".format(shared_target_id))

    campaign_service_v10.SetTargetToAdGroup(ad_group_ids['long'][0], shared_target_id)
    output_status_message("Associated AdGroupId {0} with TargetId {1}.\n".format(ad_group_ids['long'][0], shared_target_id))
    campaign_service_v10.SetTargetToAdGroup(ad_group_ids['long'][1], shared_target_id)
    output_status_message("Associated AdGroupId {0} with TargetId {1}.\n".format(ad_group_ids['long'][1], shared_target_id))
    campaign_service_v10.SetTargetToAdGroup(ad_group_ids['long'][2], shared_target_id)
    output_status_message("Associated AdGroupId {0} with TargetId {1}.\n".format(ad_group_ids['long'][2], shared_target_id))
            
    return shared_target_id

def main(authorization_data):

    try:
        campaign_ids = get_example_campaign_ids(authorization_data)
                
        # You can set campaign_ids null to get all campaigns in the account, instead of 
        # adding and retrieving the example campaigns.

        get_campaigns=campaign_service.GetCampaignsByIds(
            AccountId=authorization_data.account_id,
            CampaignIds=campaign_ids,
            CampaignType=ALL_CAMPAIGN_TYPES
        ).Campaigns
                        
        # Loop through all campaigns and ad groups to get the target criterion IDs.

        for campaign in get_campaigns['Campaign']:
            campaign_id = campaign.Id

            # Set campaign_criterion_ids null to get all criterions 
            # (of the specified target criterion type or types) for the current campaign.

            get_campaign_criterions_by_ids_response = campaign_service.GetCampaignCriterionsByIds(
                CampaignId=campaign_id,
                CampaignCriterionIds=None,
                CriterionType=ALL_TARGET_CAMPAIGN_CRITERION_TYPES
            )
            campaign_criterions= get_campaign_criterions_by_ids_response.CampaignCriterions['CampaignCriterion'] \
                if hasattr(get_campaign_criterions_by_ids_response.CampaignCriterions, 'CampaignCriterion') \
                else None
            
            # When you first create a campaign or ad group using the Bing Ads API, it will not have any 
            # criterions. Effectively, the brand new campaign and ad group target all ages, days, hours, 
            # devices, genders, and locations. As a best practice, you should consider at a minimum 
            # adding a campaign location criterion corresponding to the customer market country.

            if campaign_criterions is None or len(campaign_criterions['CampaignCriterion']) <= 0:
                campaign_criterions=campaign_service.factory.create('ArrayOfCampaignCriterion')

                # Define the Campaign Location Criterion

                campaign_location_criterion=set_elements_to_none(campaign_service.factory.create('BiddableCampaignCriterion'))
                campaign_location_criterion.Type='BiddableCampaignCriterion'
                campaign_location_criterion.CampaignId=campaign_id

                bid_multiplier=set_elements_to_none(campaign_service.factory.create('BidMultiplier'))
                bid_multiplier.Type='BidMultiplier'
                bid_multiplier.Multiplier=0
                campaign_location_criterion.CriterionBid=bid_multiplier
                
                location_criterion=set_elements_to_none(campaign_service.factory.create('LocationCriterion'))
                location_criterion.Type='LocationCriterion'
                # United States
                location_criterion.LocationId=190
                campaign_location_criterion.Criterion=location_criterion

                campaign_criterions.CampaignCriterion.append(campaign_location_criterion)

                # Define the Campaign Location Intent Criterion

                campaign_location_intent_criterion=set_elements_to_none(campaign_service.factory.create('BiddableCampaignCriterion'))
                campaign_location_intent_criterion.Type='BiddableCampaignCriterion'
                campaign_location_intent_criterion.CampaignId=campaign_id
                
                location_intent_criterion=set_elements_to_none(campaign_service.factory.create('LocationIntentCriterion'))
                location_intent_criterion.Type='LocationIntentCriterion'
                location_intent_criterion.IntentOption='PeopleInOrSearchingForOrViewingPages'
                campaign_location_intent_criterion.Criterion=location_intent_criterion

                campaign_criterions.CampaignCriterion.append(campaign_location_intent_criterion)

                add_campaign_criterions_response = campaign_service.AddCampaignCriterions(
                    CampaignCriterions=campaign_criterions,
                    CriterionType='Targets'
                )
                
                # If the campaign used to share target criterions with another campaign or ad group,
                # and the add operation resulted in new target criterion identifiers for this campaign,
                # then we need to get the new criterion IDs.

                # Otherwise we only need to capture the new criterion IDs.

                if add_campaign_criterions_response.IsMigrated:
                    get_campaign_criterions_by_ids_response = campaign_service.GetCampaignCriterionsByIds(
                        CampaignId=campaign_id,
                        CampaignCriterionIds=None,
                        CriterionType=ALL_TARGET_CAMPAIGN_CRITERION_TYPES
                    )
                    campaign_criterions= get_campaign_criterions_by_ids_response.CampaignCriterions['CampaignCriterion'] \
                        if hasattr(get_campaign_criterions_by_ids_response.CampaignCriterions, 'CampaignCriterion') \
                        else None
                elif add_campaign_criterions_response is not None and len(add_campaign_criterions_response.CampaignCriterionIds) > 0:
                    campaign_criterion_ids={
                        'long': add_campaign_criterions_response.CampaignCriterionIds['long'] if add_campaign_criterions_response.CampaignCriterionIds['long'] else None
                    }
                    for index in range(len(campaign_criterion_ids['long'])):
                        campaign_criterions['CampaignCriterion'][index].Id = campaign_criterion_ids['long'][index]
                         
            # You can now store or output the campaign criterions, whether or not they were 
            # migrated from a shared target library.

            output_status_message("Campaign Criterions: \n")
            output_campaign_criterions(campaign_criterions)

            get_ad_groups=campaign_service.GetAdGroupsByCampaignId(
                CampaignId=campaign_id
            )

            # Loop through all ad groups to get the target criterion IDs.
            for ad_group in get_ad_groups['AdGroup']:
                ad_group_id = ad_group.Id

                # Set ad_group_criterion_ids null to get all criterions 
                # (of the specified target criterion type or types) for the current ad group.
                get_ad_group_criterions_by_ids_response = campaign_service.GetAdGroupCriterionsByIds(
                    AdGroupId=ad_group_id,
                    AdGroupCriterionIds=None,
                    CriterionType=ALL_TARGET_AD_GROUP_CRITERION_TYPES
                )
                ad_group_criterions= get_ad_group_criterions_by_ids_response \
                    if hasattr(get_ad_group_criterions_by_ids_response, 'AdGroupCriterion') \
                    else None

                # If the Smartphones device criterion already exists, we'll increase the bid multiplier by 5 percent.
 
                update_ad_group_criterions=campaign_service.factory.create('ArrayOfAdGroupCriterion')
                for ad_group_criterion in ad_group_criterions['AdGroupCriterion']:
                    if ad_group_criterion.Criterion is not None \
                       and ad_group_criterion.Criterion.Type.lower() == 'devicecriterion' \
                       and ad_group_criterion.Criterion.DeviceName.lower() == "smartphones":
                        ad_group_criterion.CriterionBid.Multiplier *= 1.05
                        update_ad_group_criterions.AdGroupCriterion.append(ad_group_criterion)
                        
                if update_ad_group_criterions is not None and len(update_ad_group_criterions) > 0:
                    update_ad_group_criterions_response = campaign_service.UpdateAdGroupCriterions(
                        AdGroupCriterions=update_ad_group_criterions,
                        CriterionType='Targets'
                    )

                    # If the ad group used to share target criterions with another campaign or ad group,
                    # and the update operation resulted in new target criterion identifiers for this ad group,
                    # then we need to get the new criterion IDs.

                    if update_ad_group_criterions_response.IsMigrated:
                        get_ad_group_criterions_by_ids_response = campaign_service.GetAdGroupCriterionsByIds(
                            AdGroupId=ad_group_id,
                            AdGroupCriterionIds=None,
                            CriterionType=ALL_TARGET_AD_GROUP_CRITERION_TYPES
                        )
                        ad_group_criterions= get_ad_group_criterions_by_ids_response \
                            if hasattr(get_ad_group_criterions_by_ids_response, 'AdGroupCriterion') \
                            else None
                        
                # You can now store or output the ad group criterions, whether or not they were 
                # migrated from a shared target library.

                output_status_message("Ad Group Criterions: ")
                output_ad_group_criterions(ad_group_criterions)

        # Delete the campaign and ad group that were previously added. 
                
        campaign_service.DeleteCampaigns(
            AccountId=authorization_data.account_id,
            CampaignIds=campaign_ids
        )

        for campaign_id in campaign_ids['long']:
            output_status_message("Deleted CampaignId {0}\n".format(campaign_id))

        output_status_message("Program execution completed")

    except WebFault as ex:
        output_webfault_errors(ex)
    except Exception as ex:
        output_status_message(ex)

# Main execution

if __name__ == '__main__':

    print("Python loads the web service proxies at runtime, so you will observe " \
          "a performance delay between program launch and main execution...\n")

    authorization_data=AuthorizationData(
        account_id=None,
        customer_id=None,
        developer_token=DEVELOPER_TOKEN,
        authentication=None,
    )

    campaign_service_v10=ServiceClient(
        service='CampaignManagementService', 
        authorization_data=authorization_data, 
        environment=ENVIRONMENT,
        version=10,
    )

    campaign_service=ServiceClient(
        service='CampaignManagementService', 
        authorization_data=authorization_data, 
        environment=ENVIRONMENT,
        version=11,
    )
    
    adinsight_service=ServiceClient(
        service='AdInsightService', 
        authorization_data=authorization_data, 
        environment=ENVIRONMENT,
        version=11
    )

    # You should authenticate for Bing Ads production services with a Microsoft Account, 
    # instead of providing the Bing Ads username and password set. 
    # Authentication with a Microsoft Account is currently not supported in Sandbox.       

    authenticate(authorization_data)       

    main(authorization_data)