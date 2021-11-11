# Amazon Lightsail 流量监控/自动关机脚本

- 环境要求python3   ```pip install awscli pytz```
- 流量监测/自动关机脚本
```
usage: transCheck.py [-h] [--traffic TRAFFIC] id key region

AWS Lightsail traffic check tools:

positional arguments:
  id                 AWS_ACCESS_KEY_ID
  key                AWS_SECRET_ACCESS_KEY
  region             AWS_REGION

optional arguments:
  -h, --help         show this help message and exit
  --traffic TRAFFIC  Debug: Use this traffic setting as the upper limit, in MByte
```

- 输出位于```data```目录下```mergeHtml.py```可以将日志合并输出为单一```index.html```

![image](https://user-images.githubusercontent.com/84311024/141241136-5b6cf63c-1800-4702-900b-64aa78116f79.png)

