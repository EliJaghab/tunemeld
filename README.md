www.tunemeld.com
- pyproject.toml -> requirements.txt: poetry export -f requirements.txt --output requirements.txt
- venv -> source venv/bin/activate
- get logs -> counter=1 && logs_url=$(aws elasticbeanstalk retrieve-environment-info --environment-name Tunemeld-env --info-type tail | jq -r '.EnvironmentInfo[].Message' | grep -o '/var/log/nginx/error\.log\|/var/log/nginx/access\.log\|/path/to/other/log1\.log\|/path/to/other/log2\.log') && filename="all_logs.log" && for url in $logs_url; do curl -s "$url" | tail -n 100 >> "$filename"; done
