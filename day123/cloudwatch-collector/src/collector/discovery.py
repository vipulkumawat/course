"""CloudWatch log group discovery engine."""
import boto3
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import time

from ..models.log_entry import LogGroupInfo


logger = logging.getLogger(__name__)


class CloudWatchDiscovery:
    """Discovers CloudWatch log groups across accounts and regions."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize discovery engine."""
        self.config = config
        self.cache: Dict[str, List[LogGroupInfo]] = {}
        self.cache_ttl = config['collector']['discovery_interval']
        self.last_discovery = {}
        
    def get_client(self, region: str, account_config: Dict[str, Any]):
        """Create CloudWatch Logs client with optional role assumption."""
        session = boto3.Session(region_name=region)
        
        # Assume role if configured
        if account_config.get('role_arn'):
            sts = session.client('sts')
            assumed_role = sts.assume_role(
                RoleArn=account_config['role_arn'],
                RoleSessionName='cloudwatch-collector',
                ExternalId=account_config.get('external_id'),
                DurationSeconds=3600
            )
            
            credentials = assumed_role['Credentials']
            session = boto3.Session(
                aws_access_key_id=credentials['AccessKeyId'],
                aws_secret_access_key=credentials['SecretAccessKey'],
                aws_session_token=credentials['SessionToken'],
                region_name=region
            )
        
        return session.client(
            'logs',
            config=boto3.session.Config(
                retries={'max_attempts': self.config['aws']['cloudwatch']['max_retries']},
                max_pool_connections=self.config['aws']['cloudwatch']['max_connections']
            )
        )
    
    def discover_log_groups(self, region: str, account_config: Dict[str, Any],
                           force: bool = False) -> List[LogGroupInfo]:
        """Discover all log groups in a region."""
        cache_key = f"{account_config['account_id']}:{region}"
        
        # Check cache
        if not force and cache_key in self.cache:
            last_update = self.last_discovery.get(cache_key, 0)
            if time.time() - last_update < self.cache_ttl:
                logger.debug(f"Using cached log groups for {cache_key}")
                return self.cache[cache_key]
        
        logger.info(f"Discovering log groups in {region} for account {account_config['account_id']}")
        
        try:
            client = self.get_client(region, account_config)
            log_groups = []
            
            # Paginate through all log groups
            paginator = client.get_paginator('describe_log_groups')
            for page in paginator.paginate():
                for lg in page['logGroups']:
                    # Get tags
                    tags = {}
                    try:
                        tag_response = client.list_tags_log_group(
                            logGroupName=lg['logGroupName']
                        )
                        tags = tag_response.get('tags', {})
                    except Exception as e:
                        logger.warning(f"Failed to get tags for {lg['logGroupName']}: {e}")
                    
                    log_group = LogGroupInfo(
                        log_group_name=lg['logGroupName'],
                        region=region,
                        account_id=account_config['account_id'],
                        creation_time=lg.get('creationTime'),
                        stored_bytes=lg.get('storedBytes'),
                        retention_days=lg.get('retentionInDays'),
                        tags=tags
                    )
                    log_groups.append(log_group)
            
            # Update cache
            self.cache[cache_key] = log_groups
            self.last_discovery[cache_key] = time.time()
            
            logger.info(f"Discovered {len(log_groups)} log groups in {cache_key}")
            return log_groups
            
        except Exception as e:
            logger.error(f"Failed to discover log groups in {cache_key}: {e}")
            # Return cached data if available
            return self.cache.get(cache_key, [])
    
    def discover_all(self, force: bool = False) -> Dict[str, List[LogGroupInfo]]:
        """Discover log groups across all configured accounts and regions."""
        all_log_groups = {}
        
        for account in self.config['aws']['accounts']:
            for region in self.config['aws']['regions']:
                key = f"{account['account_id']}:{region}"
                log_groups = self.discover_log_groups(region, account, force)
                all_log_groups[key] = log_groups
        
        return all_log_groups
