"""
Test Terraform configuration validation
"""

import pytest
import subprocess
from pathlib import Path
import json

PROJECT_ROOT = Path(__file__).parent.parent

class TestTerraformValidation:
    """Validate Terraform configurations"""
    
    @pytest.mark.parametrize("environment", ["dev", "staging", "prod"])
    def test_terraform_validate(self, environment):
        """Test that Terraform configuration is valid"""
        terraform_dir = PROJECT_ROOT / "terraform" / "environments" / environment
        
        if not terraform_dir.exists():
            pytest.skip(f"Environment {environment} not implemented")
        
        # Initialize
        result = subprocess.run(
            ["terraform", "init", "-backend=false"],
            cwd=terraform_dir,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Terraform init failed: {result.stderr}"
        
        # Validate
        result = subprocess.run(
            ["terraform", "validate"],
            cwd=terraform_dir,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Terraform validation failed: {result.stderr}"
    
    def test_aws_module_structure(self):
        """Test AWS module structure exists"""
        required_modules = ["compute", "storage", "network", "monitoring"]
        
        for module in required_modules:
            module_path = PROJECT_ROOT / "terraform" / "modules" / "aws" / module / "main.tf"
            assert module_path.exists(), f"Missing AWS module: {module}"
    
    def test_module_outputs_defined(self):
        """Test that modules define required outputs"""
        compute_module = PROJECT_ROOT / "terraform" / "modules" / "aws" / "compute" / "main.tf"
        
        with open(compute_module, 'r') as f:
            content = f.read()
            assert 'output "cluster_endpoint"' in content
            assert 'output "cluster_id"' in content

class TestDeploymentOrchestrator:
    """Test deployment orchestration"""
    
    def test_orchestrator_import(self):
        """Test that orchestrator script can be imported"""
        import sys
        sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
        
        from deploy import DeploymentOrchestrator
        
        orchestrator = DeploymentOrchestrator("dev", "aws", PROJECT_ROOT)
        assert orchestrator.environment == "dev"
        assert orchestrator.cloud_provider == "aws"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
