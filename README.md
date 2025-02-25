# FeedMatrix

FeedMatrix is a modular automation platform designed to streamline the creation and distribution of dynamic content across multiple social media profiles. The first implementation focuses on an Anime News Instagram account (AnimeUtopia), but the architecture is built to easily extend to additional accounts and platforms in the future.

## Overview

FeedMatrix automates the entire content pipeline from detecting new anime news to rendering a video post using a combination of scripting, Adobe After Effects automation, and AWS cloud services. The system performs the following steps:

1. **RSS Feed Monitoring:** A batch script fetches an RSS feed (from Anime News Network) and checks for new anime-related content.
2. **Content Extraction & Processing:** A Python script extracts key details (title, description) from the feed and uses the AniList API to verify anime titles and fetch cover images.
3. **Video Rendering:** Adobe After Effects is automated via ExtendScript to apply the fetched data (title, description, and background image) to a pre-designed template.
4. **Asset Management & Notification:** The rendered video and project files are uploaded to an AWS S3 bucket. An SNS notification is then sent via email with download links, so the final content can be manually posted on Instagram. (Sadly, I couldn't get it to post correctly **YET**)

## Architecture

The project leverages AWS and infrastructure-as-code (Terraform) to manage its components:

- **AWS Lambda Functions:** Modular functions handle discrete tasks such as fetching RSS feeds, processing content, controlling EC2 instances, rendering videos, saving outputs, and sending notifications.
- **AWS Step Functions:** Orchestrates the end-to-end workflow by triggering the Lambda functions in sequence.
- **EC2 Instance:** A dedicated Windows instance (with Adobe After Effects and Photoshop installed) handles the video rendering tasks.
- **S3 & SNS:** S3 is used for storing media assets, while SNS sends notifications upon successful content generation.
- **Terraform:** Manages the infrastructure provisioning (Lambda, Step Functions, EC2, SNS, S3, CloudWatch Events, and IAM roles/policies) for both non-production and production environments.

## Project Structure

FeedMatrix/
├── artifacts/
│   ├── adobe/
│   │   └── animeutopia/                # After Effects template, logos, and related assets
│   └── scripts/
│       └── animeutopa/                 # Lambda functions (fetch_rss, process_content, render_video, etc.)
├── tf/
│   ├── main.tf                       # Primary Terraform configuration file
│   ├── outputs.tf                    # Terraform outputs
│   ├── providers.tf                  # AWS provider configuration
│   ├── variables.tf                  # Terraform variable definitions
│   ├── backend.tf                    # Remote state configuration for Terraform
│   ├── lambda.tf                     # Definitions for Lambda functions and IAM roles/policies
│   ├── sfn.tf                        # AWS Step Functions configuration
│   ├── sns.tf                        # SNS Topic and subscription configuration
│   └── state_machine.json.tpl        # Template for Step Functions state machine definition
├── atlantis.yaml                     # Atlantis configuration for CI/CD with Terraform
├── tfvars/                           # Terraform variable files for different environments
└── backends/                         # Terraform backend configuration files

## Usage

- **Scheduled Execution:** CloudWatch Events trigger the state machine every 5 minutes. The workflow fetches the RSS feed, processes the content, and if new anime content is detected, it executes the video rendering workflow.
- **Manual Posting:** After receiving an SNS notification (with pre-signed URLs for the video and project file), the content is manually posted on Instagram. Future enhancements will aim to automate this posting process further.
- **Monitoring & Logs:** Logs from Lambda functions, the EC2 instance, and After Effects automation are available via CloudWatch and local log files for troubleshooting and performance monitoring.

## Future Enhancements

- **Platform Expansion:** Extend the automation to include more social media platforms and accounts.
- **Improved Automation:** Integrate direct posting to platforms after becoming an approved Meta developer to use it's Instagram API directly.
- **Monitoring:** Implement monitoring dashboards and alerts for system performance, error notifications, and workflow tracking.
- **Scalability:** Optimize the system for higher throughput and multi-threaded processing.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for further details.

## Contact

Feel free to contact me about anything at all:
- **Ryan Longoria**
- **Email:** [ryan.longoria.cy@gmail.com](mailto:ryan.longoria.cy@gmail.com)