| **分类** | **开发者 & 项目名称** | **简介** | **Star数** | **更新时间** |
| :----: | :----: | :----: | :----: | :----: |
{%- for item in projects %}
| App | 开发者:{{ item['owner_name'] }} <br/> 项目名:[{{ item['name'] }}]({{ item['url'] }}) | {{ item['description'] }} | {{ item['forks_count'] }} |  {{ item['pushed_at']|datetime_format }} |
{%- endfor %}