import uuid
import random
from datetime import datetime, timedelta

table_name ="knowledge_base"

class KnowledgeBaseGenerator:
    def __init__(self, services, error_patterns):
        self.services = services
        self.error_patterns = error_patterns
        # Predefined templates for remediation and RCA keyed by error message pattern
        self.remediation_rca_templates = {
            # Production Critical Errors
            "High Availability Failover Initiated": {
                "remediation": [
                    "Verify failover event details in monitoring and logs.",
                    "Check health and connectivity of both primary and secondary sites.",
                    "Analyze failover triggers and health probe configurations.",
                    "Confirm traffic routing with DNS and load balancers post-failover.",
                    "Update incident documentation and notify all stakeholders."
                ],
                "rca": [
                    "Network or hardware failure in primary region caused failover.",
                    "Health probes detected critical service unresponsiveness.",
                    "Failover policies executed as expected under availability sets.",
                    "Unexpected load or capacity constraints may have contributed.",
                    "Documented runbook gaps identified during incident review."
                ],
                "business_impact": "Service interruption impacting 15% of users leading to SLA breaches.",
                "estimated_recovery_time": "10-15 minutes"
            },
            "Database Deadlock Detected": {
                "remediation": [
                    "Identify deadlocked sessions with database diagnostics.",
                    "Terminate blocking transactions to release locks.",
                    "Optimize problematic queries and reduce lock hold times.",
                    "Implement retry mechanisms for transient deadlock errors.",
                    "Schedule intensive batch jobs during quiet periods."
                ],
                "rca": [
                    "Concurrent database transactions competing for locks.",
                    "Poor query performance and indexing increased lock duration.",
                    "Heavy batch jobs ran alongside peak transaction loads.",
                    "Application lacks proper handling for deadlock retries.",
                    "Alert thresholds were configured too high for early detection."
                ],
                "business_impact": "Transaction failures causing estimated $3,000 revenue loss within 30 minutes.",
                "estimated_recovery_time": "20-30 minutes"
            },
            "SSL Certificate Expiration Critical": {
                "remediation": [
                    "Renew SSL certificate with certificate authority or Key Vault.",
                    "Deploy renewed certificates to affected Azure services.",
                    "Restart services to enable new certificate usage.",
                    "Set up automated certificate monitoring and alerting.",
                    "Document certificate lifecycle and renewal procedures."
                ],
                "rca": [
                    "Automatic renewal scripts failed due to permission errors.",
                    "No fallback manual renewal process in place.",
                    "Monitoring for upcoming expiry was inadequate.",
                    "Poor communication among DevOps and security teams.",
                    "Incomplete certificate management documentation."
                ],
                "business_impact": "User connectivity blocked causing compliance risks and loss of trust.",
                "estimated_recovery_time": "30-60 minutes"
            },
            "Memory Resource Exhaustion": {
                "remediation": [
                    "Scale up memory resources or add more instances.",
                    "Run memory profiling to identify leaks or spikes.",
                    "Optimize or fix memory-intensive code paths.",
                    "Restart services or redeploy containers.",
                    "Configure alerts on memory usage thresholds."
                ],
                "rca": [
                    "Memory leaks due to inefficient caching algorithms.",
                    "Unexpected traffic spikes overwhelmed allocated resources.",
                    "Inadequate resource limits on containerized workloads.",
                    "Garbage collection inadequacies in runtime environment.",
                    "Monitoring lacked predictive alerts."
                ],
                "business_impact": "Service slowdowns with intermittent failures affecting users intermittently.",
                "estimated_recovery_time": "30-60 minutes"
            },
            "Azure Front Door Service Disruption": {
                "remediation": [
                    "Check Azure status for known outages.",
                    "Restart or reconfigure Front Door configurations.",
                    "Validate backend health probes and routing.",
                    "Engage Microsoft support if issue persists.",
                    "Update DNS and cache settings as required."
                ],
                "rca": [
                    "Platform-level service issue or global Azure outage.",
                    "Misconfiguration of routing or backend health endpoints.",
                    "Caching or SSL errors causing disruption.",
                    "Incomplete failover or disaster recovery plans.",
                    "Software bugs in Front Door service."
                ],
                "business_impact": "Broad traffic impact causing significant brand and revenue effects.",
                "estimated_recovery_time": "Up to several hours"
            },
            "Azure SQL Database Connection Timeout": {
                "remediation": [
                    "Monitor and reset stale or hung connections.",
                    "Increase connection pool timeouts and sizes.",
                    "Review firewall and network security rules.",
                    "Scale database resources to handle load.",
                    "Implement query performance improvements."
                ],
                "rca": [
                    "Exhausted database connection pools.",
                    "Network latency or firewall misconfigurations.",
                    "Long-running queries blocking connections.",
                    "Excessive concurrent connection attempts.",
                    "Application lacked effective retry logic."
                ],
                "business_impact": "Delayed business transactions and workflow interruptions.",
                "estimated_recovery_time": "15-30 minutes"
            },
            "Azure VM Unresponsive": {
                "remediation": [
                    "Restart VM from Azure portal or CLI.",
                    "Check boot diagnostics for errors.",
                    "Review recent configuration and updates.",
                    "Verify network and NSG rules.",
                    "Scale or replace VM if persistent."
                ],
                "rca": [
                    "Kernel panics or crashes due to faulty drivers.",
                    "Disk or hardware failures.",
                    "Startup script errors or misconfigurations.",
                    "Failed OS patches or updates.",
                    "Underlying host hardware issues."
                ],
                "business_impact": "Critical workload outages and service disruption.",
                "estimated_recovery_time": "30-60 minutes"
            },
            "Managed Disk Failure": {
                "remediation": [
                    "Replace or restore managed disks.",
                    "Verify backups and snapshots.",
                    "Monitor disk health and encryption.",
                    "Engage support for suspected hardware failures.",
                    "Test recovery and redundancy plans."
                ],
                "rca": [
                    "Storage hardware faults.",
                    "Disk corruption or metadata issues.",
                    "Misconfigured backup or snapshot policies.",
                    "Azure software stack bugs.",
                    "Insufficient redundancy or disaster recovery."
                ],
                "business_impact": "Partial or total data unavailability risk.",
                "estimated_recovery_time": "1-2 hours"
            },
            "Azure Load Balancer Health Probe Failed": {
                "remediation": [
                    "Check health endpoints for responsiveness.",
                    "Adjust probe timeout and intervals.",
                    "Review NSG and firewall settings.",
                    "Restart backend instances.",
                    "Reconfigure load balancer pools."
                ],
                "rca": [
                    "Backend application failures or crashes.",
                    "Network blocking probe traffic.",
                    "Resource exhaustion on backend VMs.",
                    "Misconfiguration of probes.",
                    "Deadlocks or application hangs."
                ],
                "business_impact": "Traffic misrouting causing service downtime.",
                "estimated_recovery_time": "15-30 minutes"
            },
            "Azure Key Vault Access Denied": {
                "remediation": [
                    "Audit and update RBAC and access policies.",
                    "Check managed identities and token validity.",
                    "Implement least privilege access.",
                    "Enable logging on access events.",
                    "Conduct periodic access reviews."
                ],
                "rca": [
                    "Revoked or misconfigured permissions.",
                    "Expired authentication tokens.",
                    "Cross-subscription access issues.",
                    "Human error in role assignments.",
                    "Lack of monitoring on policy changes."
                ],
                "business_impact": "Deployment delays and secret retrieval failures.",
                "estimated_recovery_time": "15-30 minutes"
            },
                             
          # Production High-Severity Errors (sample)

            "Elevated Error Rate Detected": {
                "remediation": [
                    "Analyze application and service logs to identify error patterns.",
                    "Scale up impacted services or API gateways temporarily.",
                    "Implement circuit breaker and retry mechanisms to isolate failures.",
                    "Review recent deployments or configuration changes for regressions.",
                    "Enhance monitoring with proactive alert thresholds and anomaly detection."
                ],
                "rca": [
                    "Sudden traffic spikes exceeding capacity led to resource exhaustion.",
                    "Application bugs introduced during recent releases.",
                    "Dependency failures in backend services causing cascading errors.",
                    "Inadequate load testing and capacity planning.",
                    "Insufficient error handling propagated failures."
                ],
                "business_impact": "User experience degraded, increased failed transactions and revenue risk.",
                "estimated_recovery_time": "15-45 minutes"
            },
            "Network Connectivity Issues": {
                "remediation": [
                    "Investigate network device and virtual network health in affected regions.",
                    "Inspect firewall, NSG, and routing configurations for errors or blocks.",
                    "Check Azure service status and outage reports.",
                    "Restart network interfaces or affected services if required.",
                    "Coordinate with Azure support if issues persist."
                ],
                "rca": [
                    "Transient or persistent network hardware failures.",
                    "Misconfigured network security rules blocking traffic.",
                    "Routing table or DNS misconfigurations.",
                    "Azure infrastructure outages or maintenance.",
                    "Faulty load balancer or VPN gateway components."
                ],
                "business_impact": "Intermittent or complete loss of connectivity impacting business workflows.",
                "estimated_recovery_time": "30-120 minutes"
            },
            "Database Performance Degradation": {
                "remediation": [
                    "Use query performance insights to identify slow or blocking queries.",
                    "Add indexes or refactor queries to improve efficiency.",
                    "Scale database resources such as DTUs or vCores.",
                    "Monitor wait stats and lock escalations.",
                    "Review and tune database configuration parameters."
                ],
                "rca": [
                    "High query volume causing resource saturation.",
                    "Blocking and deadlocks increasing latency.",
                    "Inefficient query plans due to missing indexes.",
                    "Resource limits hit on database tier.",
                    "Unexpected growth in data size and usage patterns."
                ],
                "business_impact": "Slowed transactions leading to delayed user operations and revenue impact.",
                "estimated_recovery_time": "20-40 minutes"
            },
            "Azure App Service HTTP 5xx Errors": {
                "remediation": [
                    "Analyze application logs and error traces for root causes.",
                    "Scale out App Service plans to handle loads.",
                    "Investigate recent deployments for regressions.",
                    "Check dependencies like databases or APIs for issues.",
                    "Enable health checks and auto-healing to reduce downtime."
                ],
                "rca": [
                    "Application crashes or unhandled exceptions under load.",
                    "Resource exhaustion such as CPU or memory limits.",
                    "Faulty code or misconfiguration causing service failures.",
                    "Backend dependency outages cascading to frontend errors.",
                    "Delayed deployments introducing instability."
                ],
                "business_impact": "Downtime of web services causing reduced engagement and lost revenue.",
                "estimated_recovery_time": "10-30 minutes"
            },
            "Azure Functions Execution Timeout": {
                "remediation": [
                    "Review function execution times against configured timeouts.",
                    "Optimize function code and dependencies for better performance.",
                    "Scale function plans or switch to premium plans as needed.",
                    "Investigate external service call latencies affecting functions.",
                    "Implement asynchronous or durable functions for long-running tasks."
                ],
                "rca": [
                    "Long-running synchronous operations blocking completion.",
                    "Network delays or dependent service slowness.",
                    "Insufficient plan capacity causing cold starts.",
                    "Suboptimal function code or dependencies.",
                    "Lack of retries or fallback mechanisms."
                ],
                "business_impact": "Partial processing failure affecting workflows and user experiences.",
                "estimated_recovery_time": "15-45 minutes"
            },
            "Azure Storage Throttling": {
                "remediation": [
                    "Monitor storage account metrics and throttling alerts.",
                    "Distribute workload across multiple storage accounts if possible.",
                    "Optimize storage access patterns and batch operations.",
                    "Use retry logic with exponential backoff on throttled requests.",
                    "Upgrade storage account SKU for greater throughput."
                ],
                "rca": [
                    "High number of concurrent requests exceeding throughput limits.",
                    "Burst traffic patterns without load smoothing.",
                    "Inefficient access via small or repeated transactions.",
                    "Misconfiguration limiting available resources.",
                    "Absence of retry handling on throttled requests."
                ],
                "business_impact": "Delayed data access and processing impacting application performance.",
                "estimated_recovery_time": "20-60 minutes"
            },
            "API Management Gateway Latency": {
                "remediation": [
                    "Analyze gateway and backend telemetry for latency sources.",
                    "Scale API Management units or cache frequently used responses.",
                    "Optimize backend APIs and reduce response sizes.",
                    "Distribute traffic with regional API gateways if needed.",
                    "Implement throttling policies to prevent overload."
                ],
                "rca": [
                    "Backend service delays propagated to API gateway.",
                    "Resource constraints on gateway affecting throughput.",
                    "Large or complex API responses increasing processing time.",
                    "High volume of concurrent API calls causing queueing.",
                    "Insufficient scaling or caching strategies."
                ],
                "business_impact": "Slowed API responses affecting client applications and workflows.",
                "estimated_recovery_time": "15-45 minutes"
            },
            "Azure Cosmos DB RU Throttling": {
                "remediation": [
                    "Monitor request unit (RU) consumption and adjust provisioned throughput.",
                    "Implement retry logic with exponential backoff in clients.",
                    "Optimize queries and partition keys to improve efficiency.",
                    "Distribute workloads to avoid hotspots.",
                    "Use autoscale or serverless throughput models where applicable."
                ],
                "rca": [
                    "Exceeded provisioned RU limits causing request throttling.",
                    "Inefficient queries requiring excessive RU consumption.",
                    "Uneven data distribution creating partition hotspots.",
                    "Sudden spikes in traffic without scaling.",
                    "Lack of client-side retry and error handling."
                ],
                "business_impact": "Request failures impacting user operations and application reliability.",
                "estimated_recovery_time": "15-30 minutes"
            },
            "Azure Monitor Alert Triggered": {
                "remediation": [
                    "Review alert details and triggered conditions.",
                    "Validate alert configuration and thresholds for accuracy.",
                    "Investigate underlying resources and logs for root causes.",
                    "Tune alert rules to reduce false positives.",
                    "Implement automated responses or escalation procedures."
                ],
                "rca": [
                    "Resource thresholds crossed due to load or faults.",
                    "Misconfigured alert thresholds or duplication.",
                    "Transient or resolved issues triggering alerts.",
                    "Insufficient contextual data for accurate alerting.",
                    "Lack of fine-tuned monitoring for specific workloads."
                ],
                "business_impact": "Operational disruptions and increased incident response workload.",
                "estimated_recovery_time": "Variable based on alert cause"
            },

            # UAT Critical Errors
            "Test Failover Simulation": {
                "remediation": [
                    "Coordinate failover tests during off-hours.",
                    "Monitor all components during tests.",
                    "Update failover documentation.",
                    "Communicate schedules clearly.",
                    "Validate recovery and rollback plans."
                ],
                "rca": [
                    "Planned downtime for failover testing.",
                    "Automation gaps.",
                    "Communication issues.",
                    "Limited monitoring coverage.",
                    "Incomplete test scenarios."
                ],
                "business_impact": "Test environment unavailability; no production impact.",
                "estimated_recovery_time": "30 minutes"
            },
            "Load Test Resource Exhaustion": {
                "remediation": [
                    "Scale resources for load tests.",
                    "Monitor resource utilization.",
                    "Implement rate limiting.",
                    "Schedule tests during low traffic.",
                    "Analyze and optimize resource usage."
                ],
                "rca": [
                    "Resource starvation due to excessive load.",
                    "Insufficient scaling.",
                    "Missing throttling policies.",
                    "Unoptimized test configurations.",
                    "Lack of monitoring during tests."
                ],
                "business_impact": "Test environment degradation with delayed results.",
                "estimated_recovery_time": "1 hour"
            },
            "Integration Test Failure": {
                "remediation": [
                    "Review test logs and failed steps.",
                    "Fix service dependencies and mocks.",
                    "Update test data and configurations.",
                    "Automate test validations.",
                    "Improve pipeline stability."
                ],
                "rca": [
                    "Service API changes without proper versioning.",
                    "Unstable test data.",
                    "Pipeline misconfiguration.",
                    "External dependency failures.",
                    "Improper isolation of environments."
                ],
                "business_impact": "Delayed release validation and feedback.",
                "estimated_recovery_time": "2 hours"
            },

            # Development Critical Errors
            "Build Pipeline Failure": {
                "remediation": [
                    "Analyze and fix broken builds.",
                    "Resolve dependency conflicts.",
                    "Update pipeline configurations.",
                    "Apply pre-commit checks.",
                    "Improve developer documentation."
                ],
                "rca": [
                    "Code breakages in merges.",
                    "Missing dependencies.",
                    "Expired credentials.",
                    "Flaky tests.",
                    "Environment mismatches."
                ],
                "business_impact": "Development delays; no direct user impact.",
                "estimated_recovery_time": "1-2 hours"
            },
            "Development Database Corruption": {
                "remediation": [
                    "Restore from backups.",
                    "Validate data integrity.",
                    "Audit deployment/change processes.",
                    "Implement change control.",
                    "Monitor for future corruption."
                ],
                "rca": [
                    "Failed migrations or incompatible changes.",
                    "Software bugs.",
                    "Inadequate backups.",
                    "Hardware or shutdown faults.",
                    "Poor environment isolation."
                ],
                "business_impact": "Developer productivity loss; no production impact.",
                "estimated_recovery_time": "2-3 hours"
            },
            "Local Emulator Crash": {
                "remediation": [
                    "Restart emulator services.",
                    "Update emulator and dependencies.",
                    "Check system resource availability.",
                    "Monitor logs for crash patterns.",
                    "Apply patches or rollbacks as needed."
                ],
                "rca": [
                    "Resource exhaustion.",
                    "Software bugs.",
                    "Incompatible configuration.",
                    "Third-party dependency failures.",
                    "Unstable test scenarios."
                ],
                "business_impact": "Development workflow interruptions.",
                "estimated_recovery_time": "30-60 minutes"
            },
            "Docker Container Start Failure": {
                "remediation": [
                    "Inspect container logs for errors.",
                    "Validate image integrity and tags.",
                    "Check resource availability.",
                    "Rebuild and redeploy images.",
                    "Fix configuration or dependency issues."
                ],
                "rca": [
                    "Image corruption or misconfiguration.",
                    "Insufficient system resources.",
                    "Dependency missing or incompatible versions.",
                    "Incorrect container startup parameters.",
                    "Networking or storage misconfiguration."
                ],
                "business_impact": "Blocked local testing and development.",
                "estimated_recovery_time": "30-60 minutes"
            },

 
            # UAT High Severity Errors
            "Performance Test Threshold Breach": {
                "remediation": [
                    "Analyze test load and resource metrics for bottlenecks.",
                    "Scale up UAT resources temporarily during tests.",
                    "Tune application and database configurations for performance.",
                    "Optimize test scripts and reduce unnecessary load.",
                    "Implement more granular monitoring and alert thresholds."
                ],
                "rca": [
                    "Resource limits exceeded due to unanticipated test volume.",
                    "Inefficient query patterns slowed responses.",
                    "Load test scripts generated unrealistic usage peaks.",
                    "Scaling policies were not configured for test environments.",
                    "Lack of prior capacity planning for performance tests."
                ],
                "business_impact": "Delayed feedback on application readiness affecting release schedule.",
                "estimated_recovery_time": "1-2 hours"
            },
            "API Integration Failure": {
                "remediation": [
                    "Review API endpoint health and auth credentials.",
                    "Test API calls and validate request/response schemas.",
                    "Update API client versions and dependencies.",
                    "Increase logging and monitor API latency and errors.",
                    "Establish retry policies for transient failures."
                ],
                "rca": [
                    "Endpoint outages or misconfigurations.",
                    "Expired or invalid authentication tokens.",
                    "Version mismatch between client and API server.",
                    "Insufficient timeout and error handling in client.",
                    "Lack of testing integration points in the pipeline."
                ],
                "business_impact": "Integration test delays with cascading impact on release.",
                "estimated_recovery_time": "30-60 minutes"
            },
            "Data Sync Issues": {
                "remediation": [
                    "Check synchronization job logs and error reports.",
                    "Restart or reschedule failed sync jobs.",
                    "Validate data integrity and consistency post-sync.",
                    "Optimize sync job configurations and data volume handling.",
                    "Set up alerts for sync failures and performance degradations."
                ],
                "rca": [
                    "Transient network issues disrupting sync.",
                    "Data conflicts or schema mismatches causing failures.",
                    "Resource contention during peak processing times.",
                    "Incorrect job scheduling or overlapping sync tasks.",
                    "Lack of automated recovery procedures."
                ],
                "business_impact": "Inconsistent test data delaying validation activities.",
                "estimated_recovery_time": "45-90 minutes"
            },
            "API Rate Limit Exceeded": {
                "remediation": [
                    "Implement rate limiting and throttling policies in tests.",
                    "Optimize API consumption in test scripts.",
                    "Coordinate API usage across multiple teams.",
                    "Monitor API usage and alert on threshold breaches.",
                    "Request increased rate limits from API providers if needed."
                ],
                "rca": [
                    "Excessive parallel API requests during load testing.",
                    "Missing or misconfigured rate limiting in test environments.",
                    "Multiple concurrent integrations overwhelming API quota.",
                    "Lack of coordination between testing teams.",
                    "Insufficient monitoring of API consumption."
                ],
                "business_impact": "Test failures and delays affecting integration cycles.",
                "estimated_recovery_time": "30-60 minutes"
            },
            "Azure Service Principal Permission Denied": {
                "remediation": [
                    "Validate and update service principal RBAC assignments.",
                    "Renew service principal credentials if expired.",
                    "Audit recent permission or policy changes.",
                    "Test service principal access on affected resources.",
                    "Implement monitoring for permission denial events."
                ],
                "rca": [
                    "Revoked or expired permissions on service principal.",
                    "Policy changes restricting access unexpectedly.",
                    "Misconfiguration in identity or role assignments.",
                    "Lack of alerting on permission issues.",
                    "Changes without proper change management."
                ],
                "business_impact": "Failure to deploy or manage resources delaying UAT.",
                "estimated_recovery_time": "15-30 minutes"
            },

            # Development High Severity Errors
            "Development API Gateway Issues": {
                "remediation": [
                    "Analyze gateway logs and remove faulty configurations.",
                    "Restart API gateway services or clusters.",
                    "Scale or add nodes to handle loads.",
                    "Apply patches or roll back problematic updates.",
                    "Improve rate limiting and error handling strategies."
                ],
                "rca": [
                    "Configuration errors introduced in recent changes.",
                    "Resource exhaustion due to under-sizing.",
                    "Software bugs or incompatibility in gateway release.",
                    "Excessive or malformed traffic patterns in testing.",
                    "Insufficient monitoring and alerting coverage."
                ],
                "business_impact": "Blocking development testing and slowing feature rollout.",
                "estimated_recovery_time": "30-60 minutes"
            },
            "Local Development Stack Error": {
                "remediation": [
                    "Check error logs and stack traces thoroughly.",
                    "Restart development environment components.",
                    "Update dependencies and validate configuration files.",
                    "Resolve version conflicts among libraries.",
                    "Educate developers on environment setup best practices."
                ],
                "rca": [
                    "Dependency mismatches or conflicts.",
                    "Incorrect environment variable setups.",
                    "Corrupted local caches or build artifacts.",
                    "Outdated or incompatible software versions.",
                    "Insufficient environment documentation."
                ],
                "business_impact": "Developer productivity impacted with delayed deliveries.",
                "estimated_recovery_time": "1-2 hours"
            },
            "Test Data Generation Failure": {
                "remediation": [
                    "Verify scripts and pipelines generating test data.",
                    "Check storage availability and connectivity.",
                    "Handle errors with retry or fallback mechanisms.",
                    "Ensure schema compatibility and validation.",
                    "Automate alerts on test data pipeline failures."
                ],
                "rca": [
                    "Broken scripts or pipeline misconfigurations.",
                    "Resource or quota exhaustion in storage systems.",
                    "Schema changes not reflected in data generator.",
                    "Transient network or permission errors.",
                    "Lack of monitoring on data pipeline health."
                ],
                "business_impact": "Delayed testing cycles due to unavailable or corrupt test data.",
                "estimated_recovery_time": "1-3 hours"
            },
            "Code Repository Merge Conflicts": {
                "remediation": [
                    "Educate developers on merge conflict resolution practices.",
                    "Enable PR reviews and automated conflict checks.",
                    "Encourage frequent syncing with main branch.",
                    "Implement branching strategies to limit conflicts.",
                    "Use merge tools and automation aids appropriately."
                ],
                "rca": [
                    "Simultaneous changes on same code areas.",
                    "Lack of communication among development teams.",
                    "Poor branching and release strategy.",
                    "Insufficient automated checks pre-merge.",
                    "Rushed merges without conflict resolution steps."
                ],
                "business_impact": "Development slowdowns and rework on code merges.",
                "estimated_recovery_time": "2-4 hours"
            },
            "Unit Test Failures": {
                "remediation": [
                    "Analyze failed tests and update based on recent changes.",
                    "Fix flaky tests and improve test stability.",
                    "Automate consistent test environment setup.",
                    "Increase test coverage and update deprecated tests.",
                    "Integrate unit testing rigorously in CI pipelines."
                ],
                "rca": [
                    "Code changes breaking existing tests.",
                    "Unstable or environment-dependent test cases.",
                    "Incomplete mock or stub implementations.",
                    "Test suites not updated with API or business logic changes.",
                    "Insufficient test isolation leading to side effects."
                ],
                "business_impact": "Reduced confidence in code quality delaying releases.",
                "estimated_recovery_time": "1-3 hours"
            }

            # Add more detailed templates based on other errors here...
        }

    def choose_error(self, env):
        severity = random.choice(list(self.error_patterns[env].keys()))
        error = random.choice(self.error_patterns[env][severity])
        return severity, error

    def select_service_by_error(self, error):
        # Simplified heuristic to map error keywords to services
        if "Database" in error or "Deadlock" in error or "SQL" in error:
            return "Microsoft.Sql"
        if "SSL" in error or "Certificate" in error or "Key Vault" in error:
            return "Microsoft.KeyVault"
        if "App Service" in error or "Web" in error or "Http" in error:
            return "Microsoft.Web"
        if "Storage" in error or "Blob" in error or "Queue" in error:
            return "Microsoft.Storage"
        if "Failover" in error or "Availability" in error or "Load Balancer" in error:
            return random.choice(["Microsoft.Sql", "Microsoft.Web", "Microsoft.Storage"])
        # Default service
        return random.choice(list(self.services.keys()))

    def generate_knowledge_record(self, env):
        severity, error = self.choose_error(env)
        service = self.select_service_by_error(error)
        template = self.remediation_rca_templates.get(error, {
            "remediation": ["Investigate logs.", "Root cause analysis needed."],
            "rca": ["Root cause unknown."],
            "business_impact": "Potential impact to service availability.",
            "estimated_recovery_time": "Varies"
        })

        # (the rest of your code unchanged...)

        # Map error keywords to resource_type
        if "Database" in error or "Deadlock" in error or "SQL" in error:
            resource_type = "Azure SQL Database"
        elif "SSL" in error or "Certificate" in error or "Key Vault" in error:
            resource_type = "Azure Key Vault"
        elif "App Service" in error or "Web" in error or "Http" in error:
            resource_type = "Azure App Service"
        elif "Storage" in error or "Blob" in error or "Queue" in error:
            resource_type = "Azure Storage"
        elif "Failover" in error or "Availability" in error or "Load Balancer" in error:
            resource_type = random.choice(["Azure SQL Database", "Azure App Service", "Azure Storage"])
        elif "VM" in error or "Kernel" in error or "Managed Disk" in error:
            resource_type = "Azure VM"
        elif "RBAC" in error or "Permission" in error or "Access Denied" in error:
            resource_type = "Identity/Access"
        else:
            resource_type = random.choice(list(self.services.keys()))

        # Generate dollar impact based on environment and severity
        dollar_impact = "$0 (development only)"
        if env == "prod":
            if severity == "critical" or severity == "high":
                dollar_impact = f"${random.randint(5000, 20000):,}"
            elif severity == "medium":
                dollar_impact = f"${random.randint(1000, 5000):,}"
            else:
                dollar_impact = f"${random.randint(100, 999):,}"
        elif env == "uat":
            dollar_impact = f"${random.randint(100, 2000):,}"
        
        record_id = str(uuid.uuid4())
        description = f"{service} reported a {error} classified as {severity} in {env.upper()} environment."
        impact = f"Affected service operations causing degradation or failures impacting users and business."
        remediation_steps = ". ".join(f"{idx+1}. {step}" for idx, step in enumerate(template["remediation"]))
        rca = ". ".join(f"{idx+1}. {item}" for idx, item in enumerate(template["rca"]))
        business_impact = template["business_impact"]
        estimated_recovery_time = template["estimated_recovery_time"]

        return {
            "id": record_id,
            "cause": error,
            "description": description,
            "impact": impact,
            "remediation_steps": remediation_steps,
            "rca": rca,
            "business_impact": business_impact,
            "estimated_recovery_time": estimated_recovery_time,
            "environment": env.upper(),
            "dollar_impact": dollar_impact,
            "resource_type": resource_type
        }


services = {
    "Microsoft.KeyVault": {
        "type": "vaults",
        "operations": [
            "VaultGet", "KeyGet", "KeyCreate", "KeyDelete", "SecretGet",
            "SecretSet", "SecretDelete", "CertificateCreate", "CertificateImport", "CertificateDelete"
        ],
        "resultTypes": ["Success", "Failed", "Unauthorized", "NotFound"],
        "metrics": ["ServiceApiLatency", "RequestCount", "ThrottledRequests", "Availability", "SaturationShoebox"],
        "diagnostic_categories": [
            "AuditEvent", "AzurePolicyEvaluation", "Request", "Authentication",
            "SecretManagement", "KeyManagement", "CertificateManagement"
        ]
    },
    "Microsoft.Sql": {
        "type": "servers/databases",
        "operations": [
            "DatabaseConnect", "QueryExecute", "BackupComplete", "DatabaseFailover", "Login", "Logout",
            "Deadlock", "SchemaChange", "SecurityAudit", "DataWrite", "DataRead"
        ],
        "resultTypes": ["Succeeded", "Failed", "Timeout", "Blocked"],
        "metrics": [
            "cpu_percent", "storage_percent", "dtu_consumption_percent", "deadlock_count",
            "failed_connections", "successful_connections", "query_duration_ms"
        ],
        "diagnostic_categories": [
            "SQLSecurityAuditEvents", "AutomaticTuning", "QueryStoreRuntimeStatistics",
            "QueryStoreWaitStatistics", "Error"
        ]
    },
    "Microsoft.Web": {
        "type": "sites",
        "operations": [
            "AppServicePlanUpdate", "WebAppRestart", "SiteConfigUpdate", "AppDeployment",
            "SlotSwap", "AppScaling"
        ],
        "resultTypes": ["Succeeded", "Failed", "InProgress", "Timeout"],
        "metrics": [
            "Http5xx", "Http4xx", "ResponseTime", "CpuTime", "MemoryWorkingSet", "DataIn", "DataOut", "DiskQueueLength"
        ],
        "diagnostic_categories": [
            "AppServiceHTTPLogs", "AppServiceConsoleLogs", "DetailedErrorMessages", "FailedRequestsTracing", "AppServiceEvents"
        ]
    },
    "Microsoft.Storage": {
        "type": "storageAccounts",
        "operations": [
            "BlobGet", "BlobCreate", "BlobDelete", "ContainerDelete", "StorageRead",
            "StorageWrite", "QueueMessageProcess", "FileOperation"
        ],
        "resultTypes": ["Success", "Failed", "Timeout", "Throttled"],
        "metrics": [
            "Availability", "Transactions", "SuccessE2ELatency", "Ingress", "Egress", "ThrottlingError"
        ],
        "diagnostic_categories": [
            "StorageRead", "StorageWrite", "StorageDelete", "StorageFailure", "Authentication", "Authorization"
        ]
    }
}

error_patterns = {
    "prod": {
        "critical": [
            "High Availability Failover Initiated", "Database Deadlock Detected", "SSL Certificate Expiration Critical",
            "Memory Resource Exhaustion", "Azure Front Door Service Disruption", "Azure SQL Database Connection Timeout",
            "Azure VM Unresponsive", "Managed Disk Failure", "Azure Load Balancer Health Probe Failed",
            "Azure Key Vault Access Denied"
        ],
        "high": [
            "Elevated Error Rate Detected", "Network Connectivity Issues", "Database Performance Degradation",
            "Azure App Service HTTP 5xx Errors", "Azure Functions Execution Timeout", "Azure Storage Throttling",
            "API Management Gateway Latency", "Azure Cosmos DB RU Throttling", "Azure Monitor Alert Triggered"
        ]
    },
    "uat": {
        "critical": [
            "Test Failover Simulation", "Load Test Resource Exhaustion", "Integration Test Failure",
            "Azure DevOps Pipeline Failure", "Azure Resource Deployment Failure"
        ],
        "high": [
            "Performance Test Threshold Breach", "API Integration Failure", "Data Sync Issues",
            "API Rate Limit Exceeded", "Azure Service Principal Permission Denied"
        ]
    },
    "dev": {
        "critical": [
            "Development Environment Down", "Build Pipeline Failure", "Development Database Corruption",
            "Local Emulator Crash", "Docker Container Start Failure"
        ],
        "high": [
            "Development API Gateway Issues", "Local Development Stack Error", "Test Data Generation Failure",
            "Code Repository Merge Conflicts", "Unit Test Failures"
        ]       
    }
}


def run(conn):
    total_records = 2000
    envs = ['prod', 'uat', 'dev']
    env_distribution = {
        'prod': int(total_records * 0.5),
        'uat': int(total_records * 0.3),
        'dev': int(total_records * 0.2)
    }

    generator = KnowledgeBaseGenerator(services, error_patterns)
    conn.execute("DELETE FROM knowledge_base")

    records_created = 0
    for env in envs:
        count = env_distribution[env]
        for _ in range(count):
            record = generator.generate_knowledge_record(env)

            created_at = datetime.utcnow() - timedelta(minutes=random.randint(0, 1440))

            conn.execute("""
                INSERT INTO knowledge_base
                (id, cause, description, impact, remediation_steps, rca, business_impact, estimated_recovery_time, dollar_impact, resource_type, environment, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record["id"],
                record["cause"],
                record["description"],
                record["impact"],
                record["remediation_steps"],
                record["rca"],
                record["business_impact"],
                record["estimated_recovery_time"],
                record["dollar_impact"],
                record["resource_type"],
                env.upper(),
                created_at.isoformat(sep=' ', timespec='seconds')
            ))

            records_created += 1
            

    conn.commit()

    # Print summary grouped by environment
    cursor = conn.execute("""
        SELECT environment, COUNT(*) as count
        FROM knowledge_base
        GROUP BY environment
    """)

    print("\nKnowledge base data generation and insertion completed!")
