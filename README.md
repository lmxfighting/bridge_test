API使用方法：
打开 Postman，创建一个新的请求。选择 POST 方法，并设置 URL 为：http://127.0.0.1:5000/backtest
切换到 "Body" 选项卡，选择 raw，然后选择 JSON 格式，输入以下请求体：
{
  "file_path": "pingan.csv"
}
创建一个新的请求，选择 GET 方法，并设置 URL 为：http://127.0.0.1:5000/backtest_result
发送请求，查看返回的 final_value（最终资产总值）和 return_on_investment（收益率）。


PS：我的tushare积分后面不够了，失去了访问权限，所以只能通过读取csv文件获取股票数据。
运行结果如图所示：https://github.com/user-attachments/assets/9cf085a8-cd97-4ebe-8feb-1ac6344ddcec

