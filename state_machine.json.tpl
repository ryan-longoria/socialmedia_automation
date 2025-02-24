{
  "Comment": "State machine for automating anime post workflow",
  "StartAt": "FetchRSS",
  "States": {
    "FetchRSS": {
      "Type": "Task",
      "Resource": "${fetch_rss_arn}",
      "ResultPath": "$.rssData",
      "Next": "CheckPost"
    },
    "CheckPost": {
      "Type": "Choice",
      "Choices": [
        {
          "Variable": "$.rssData.status",
          "StringEquals": "anime_post_found",
          "Next": "StartEC2"
        }
      ],
      "Default": "EndWorkflow"
    },
    "StartEC2": {
      "Type": "Task",
      "Resource": "${start_instance_arn}",
      "ResultPath": "$.ec2StartResult",
      "Next": "ProcessContent"
    },
    "ProcessContent": {
      "Type": "Task",
      "Resource": "${process_content_arn}",
      "ResultPath": "$.processedContent",
      "Next": "StoreData"
    },
    "StoreData": {
      "Type": "Task",
      "Resource": "${store_data_arn}",
      "ResultPath": "$.storeResult",
      "Next": "RenderVideo"
    },
    "RenderVideo": {
      "Type": "Task",
      "Resource": "${render_video_arn}",
      "ResultPath": "$.videoResult",
      "Next": "SaveVideo"
    },
    "SaveVideo": {
      "Type": "Task",
      "Resource": "${save_video_arn}",
      "ResultPath": "$.saveVideoResult",
      "Next": "StopEC2"
    },
    "StopEC2": {
      "Type": "Task",
      "Resource": "${stop_instance_arn}",
      "ResultPath": "$.ec2StopResult",
      "End": true
    },
    "EndWorkflow": {
      "Type": "Succeed"
    }
  }
}
