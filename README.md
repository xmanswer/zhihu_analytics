# Zhihu-Analytics-Service
Zhihu is a Chinese question-and-answer website where questions are created, answered, edited and organized by the community of its users. This web service is developed in python for crawling large data of users and questions-answers information, as well as data storage, analysis, and visualization.

1. Crawling: a multi-threading crawling system that supports proxies crawling and validation, dynamic user-agents and proxies for anti-anti-crawling and crawling frequency control. Crawlable contents include user image, user thanks/agrees, user followers/followees, user questions/answers, user timelines, question topics/text, answers text/agrees

2. Storage: supports both on-disk file (in JSON format) storage type and database storage type. MongoDB is used as the database backend for easier scaling in future development of distributed web service

3. Analyzing: used Jieba package for Chinese text segmentation (using max likelihood route finding on sentence DAG for loaded dictionary words and HMM for unloaded words) and TF-IDF for keywords extraction. Other analysis include topic clustering, sentiment analysis, user recommendation and question recommendation.

4. Visualization: Flask framework is used for handling service queries and visualize data

APIs for crawling, keywords extraction, topic clustering, sentiment analysis and recommendation can be directly applied and embeded for developing other applications. Detailed info on APIs can be found in each module. 
