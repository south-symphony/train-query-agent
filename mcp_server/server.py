"""
MCP服务端 - 12306车次查询工具
全程调用12306官方真实接口，修复连接池问题
"""
from mcp.server.fastmcp import FastMCP
import httpx
from datetime import datetime, timedelta

# 创建MCP服务器实例
mcp = FastMCP("TrainQueryServer")

# 12306官方接口地址
QUERY_URL = "https://kyfw.12306.cn/otn/leftTicket/query"
STATION_URL = "https://kyfw.12306.cn/otn/resources/js/framework/station_name.js"
REFERER_URL = "https://kyfw.12306.cn/otn/leftTicket/init"

# 请求头
COMMON_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    "Referer": REFERER_URL,
    "Accept": "*/*",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "X-Requested-With": "XMLHttpRequest"
}

_station_map = None


def _get_station_map():
    """获取车站名称-电报码映射"""
    global _station_map
    if _station_map is not None:
        return _station_map
    
    # 每次新建客户端，避免连接池问题
    with httpx.Client(headers=COMMON_HEADERS, verify=False, follow_redirects=True, timeout=15) as client:
        try:
            response = client.get(STATION_URL)
            text = response.text
            stations = {}
            for item in text.split("@"):
                if not item:
                    continue
                parts = item.split("|")
                if len(parts) >= 3:
                    name = parts[1]
                    code = parts[2]
                    stations[name] = code
                    stations[code] = name
            _station_map = stations
            return stations
        except Exception as e:
            raise RuntimeError(f"获取车站列表失败：{str(e)}")


@mcp.tool(description="查询两个城市之间的火车车次和余票信息，数据来自12306官方接口")
def query_train_tickets(
    from_station: str,
    to_station: str,
    date: str
) -> str:
    """
    查询12306车次余票信息
    """
    # 1. 日期校验
    try:
        query_date = datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        return "错误：日期格式不正确，请使用 YYYY-MM-DD 格式，例如 2025-10-25"
    
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    max_date = today + timedelta(days=15)
    
    if query_date < today:
        return "错误：不能查询过去日期的车票"
    if query_date > max_date:
        return f"错误：超出预售期，12306仅支持查询未来15天内的车票，最远可查 {max_date.strftime('%Y-%m-%d')}"
    
    # 2. 车站转换
    stations = _get_station_map()
    from_code = stations.get(from_station)
    to_code = stations.get(to_station)
    
    if not from_code:
        return f"错误：找不到出发站「{from_station}」，请检查车站名称"
    if not to_code:
        return f"错误：找不到到达站「{to_station}」，请检查车站名称"
    
    # 3. 调用官方接口，每次新建客户端
    params = {
        "leftTicketDTO.train_date": date,
        "leftTicketDTO.from_station": from_code,
        "leftTicketDTO.to_station": to_code,
        "purpose_codes": "ADULT"
    }
    
    with httpx.Client(headers=COMMON_HEADERS, verify=False, follow_redirects=True, timeout=20) as client:
        try:
            # 先访问首页拿Cookie
            client.get(REFERER_URL)
            response = client.get(QUERY_URL, params=params)
            data = response.json()
        except Exception as e:
            return f"查询失败，网络或接口错误：{str(e)}\n12306接口可能存在临时风控，请稍后重试"
    
    # 4. 解析结果
    if data.get("httpstatus") != 200:
        return f"查询失败，接口返回异常：{data.get('messages', '未知错误')}"
    
    result = data.get("data", {}).get("result", [])
    if not result:
        return f"未查询到 {date} 从 {from_station} 到 {to_station} 的车次信息"
    
    # 5. 解析全部车次
    train_list = []
    for item in result:
        parts = item.split("|")
        if len(parts) < 33:
            continue
            
        train_no = parts[3]
        start_time = parts[8]
        arrive_time = parts[9]
        duration = parts[10]
        
        seat_second = parts[30].strip() if len(parts) > 30 else ""
        seat_first = parts[31].strip() if len(parts) > 31 else ""
        seat_business = parts[32].strip() if len(parts) > 32 else ""
        seat_hard = parts[28].strip() if len(parts) > 28 else ""
        seat_soft = parts[23].strip() if len(parts) > 23 else ""
        seat_hard_seat = parts[29].strip() if len(parts) > 29 else ""
        
        def fmt(s):
            return s if s else "--"
        
        if train_no.startswith(("G", "D", "C")):
            info = (
                f"【{train_no}】 {start_time}出发 → {arrive_time}到达  历时{duration}\n"
                f"  二等座: {fmt(seat_second)} | 一等座: {fmt(seat_first)} | 商务座: {fmt(seat_business)}"
            )
        else:
            info = (
                f"【{train_no}】 {start_time}出发 → {arrive_time}到达  历时{duration}\n"
                f"  硬座: {fmt(seat_hard_seat)} | 硬卧: {fmt(seat_hard)} | 软卧: {fmt(seat_soft)}"
            )
        train_list.append(info)
    
    if not train_list:
        return "查询成功，但暂无有效车次数据"
    
    # 组装完整结果
    result_text = f"✅ 查询成功！{date} {from_station} → {to_station} 共找到 {len(train_list)} 趟列车：\n\n"
    result_text += "\n\n".join(train_list)
    result_text += "\n\n📌 余票说明：「有」代表票量充足，数字代表剩余张数，「无」代表无票，「--」代表该车次无该席别"
    result_text += "\n📌 数据来源：12306官方成人票接口，实时更新"
    
    return result_text


@mcp.tool(description="获取支持查询的热门车站列表")
def get_supported_stations() -> str:
    stations = _get_station_map()
    city_names = [name for name in stations.keys() if '\u4e00' <= name[0] <= '\u9fff']
    hot_cities = city_names[:50]
    return "支持查询的热门城市（部分）：\n" + "、".join(hot_cities) + "\n\n支持全国所有火车站查询。"


if __name__ == "__main__":
    mcp.run(transport="stdio")
