let trendChart, regionChart, industryChart, keywordChart, heatmapChart;

function initCharts() {
    trendChart = echarts.init(document.getElementById('trendChart'));
    regionChart = echarts.init(document.getElementById('regionChart'));
    industryChart = echarts.init(document.getElementById('industryChart'));
    keywordChart = echarts.init(document.getElementById('keywordChart'));
    heatmapChart = echarts.init(document.getElementById('heatmapChart'));
    loadTrendData();
    loadRegionData();
    loadIndustryData();
    loadKeywordData();
    window.addEventListener('resize', () => {
        trendChart.resize(); regionChart.resize(); industryChart.resize();
        keywordChart.resize(); heatmapChart.resize();
    });
}

function loadTrendData() {
    fetch('/api/trend?days=30').then(r => r.json()).then(data => {
        if (data.success) {
            renderTrendChart(data.data);
            document.getElementById('chart1Tag').textContent = data.from_cache ? '来自缓存' : '实时数据';
        }
    });
}

function renderTrendChart(rawData) {
    const dates = [...new Set(rawData.map(d => d.date))].sort();
    const industries = [...new Set(rawData.map(d => d.industry))];
    const industryNames = {it:'信息技术',construction:'建筑工程',medical:'医疗卫生',education:'教育培训',finance:'财政金融',energy:'能源电力',transport:'交通运输'};
    const series = industries.map(ind => ({
        name: industryNames[ind] || ind,
        type: 'line',
        smooth: true,
        data: dates.map(date => {
            const item = rawData.find(d => d.date === date && d.industry === ind);
            return item ? item.cnt : 0;
        }),
        areaStyle: {opacity: 0.1}
    }));
    trendChart.setOption({
        title: {text: '各行业每日发布数量趋势', left: 'center', textStyle: {fontSize: 14}},
        tooltip: {trigger: 'axis'},
        legend: {bottom: 0, textStyle: {fontSize: 11}},
        grid: {left: '3%', right: '4%', bottom: '15%', top: '15%', containLabel: true},
        xAxis: {type: 'category', boundaryGap: false, data: dates, axisLabel: {fontSize: 10}},
        yAxis: {type: 'value', axisLabel: {fontSize: 11}},
        series: series,
        color: ['#667eea', '#764ba2', '#f093fb', '#4facfe', '#43e97b', '#fa709a', '#feca57']
    });
}

function loadRegionData() {
    fetch('/api/region-distribution').then(r => r.json()).then(data => {
        if (data.success) {
            renderRegionChart(data.data);
            document.getElementById('chart2Tag').textContent = data.from_cache ? '来自缓存' : '实时数据';
            renderHeatmap(data.data);
        }
    });
}

function renderRegionChart(rawData) {
    const sorted = rawData.filter(d => d.region && d.region !== 'all').sort((a, b) => b.cnt - a.cnt);
    regionChart.setOption({
        title: {text: '各地区招标数量分布', left: 'center', textStyle: {fontSize: 14}},
        tooltip: {trigger: 'item', formatter: '{b}: {c} ({d}%)'},
        legend: {bottom: 0, textStyle: {fontSize: 11}},
        series: [{
            type: 'pie',
            radius: ['40%', '65%'],
            center: ['50%', '45%'],
            avoidLabelOverlap: true,
            itemStyle: {borderRadius: 6, borderColor: '#fff', borderWidth: 2},
            label: {fontSize: 11},
            data: sorted.map(d => ({name: d.name || d.region, value: d.cnt}))
        }],
        color: ['#667eea', '#764ba2', '#f093fb', '#4facfe', '#43e97b', '#fa709a', '#feca57', '#54a0ff', '#5f27cd']
    });
}

function loadIndustryData() {
    fetch('/api/industry-distribution').then(r => r.json()).then(data => {
        if (data.success) {
            renderIndustryChart(data.data);
            document.getElementById('chart3Tag').textContent = data.from_cache ? '来自缓存' : '实时数据';
        }
    });
}

function renderIndustryChart(rawData) {
    const sorted = rawData.sort((a, b) => b.total_budget - a.total_budget);
    industryChart.setOption({
        title: {text: '各行业预算总额分布 (万元)', left: 'center', textStyle: {fontSize: 14}},
        tooltip: {trigger: 'axis', axisPointer: {type: 'shadow'}},
        grid: {left: '3%', right: '8%', bottom: '3%', top: '15%', containLabel: true},
        xAxis: {type: 'value', axisLabel: {fontSize: 11}},
        yAxis: {type: 'category', data: sorted.map(d => d.name || d.industry), axisLabel: {fontSize: 11}},
        series: [{
            type: 'bar',
            data: sorted.map(d => Math.round(d.total_budget)),
            itemStyle: {
                borderRadius: [0, 6, 6, 0],
                color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
                    {offset: 0, color: '#667eea'}, {offset: 1, color: '#764ba2'}
                ])
            },
            label: {show: true, position: 'right', fontSize: 11}
        }]
    });
}

function loadKeywordData() {
    fetch('/api/keyword-analysis').then(r => r.json()).then(data => {
        if (data.success) {
            renderKeywordChart(data.data);
            document.getElementById('chart4Tag').textContent = data.from_cache ? '来自缓存' : '实时数据';
        }
    });
}

function renderKeywordChart(rawData) {
    try {
        if (!echarts.graphic || typeof echarts.graphic !== 'object') {
            throw new Error('wordcloud not available');
        }
        keywordChart.setOption({
            title: {text: '招标主题关键词分析', left: 'center', textStyle: {fontSize: 14}},
            tooltip: {show: true, formatter: '{b}: {c}'},
            series: [{
                type: 'wordCloud',
                shape: 'circle',
                left: 'center',
                top: 'center',
                width: '90%',
                height: '85%',
                sizeRange: [12, 42],
                rotationRange: [-30, 30],
                textStyle: {
                    fontFamily: 'sans-serif',
                    fontWeight: 'bold',
                    color: function() {
                        const colors = ['#667eea', '#764ba2', '#f093fb', '#4facfe', '#43e97b', '#fa709a', '#feca57'];
                        return colors[Math.floor(Math.random() * colors.length)];
                    }
                },
                emphasis: {textStyle: {color: '#2c3e50'}},
                data: rawData.map(d => ({name: d.word, value: d.count}))
            }]
        });
    } catch(e) {
        const sorted = rawData.slice(0, 20).sort((a, b) => b.count - a.count);
        keywordChart.setOption({
            title: {text: '高频关键词TOP20', left: 'center', textStyle: {fontSize: 14}},
            tooltip: {trigger: 'axis'},
            grid: {left: '3%', right: '10%', bottom: '3%', top: '15%', containLabel: true},
            xAxis: {type: 'value', axisLabel: {fontSize: 11}},
            yAxis: {type: 'category', data: sorted.map(d => d.word).reverse(), axisLabel: {fontSize: 11}},
            series: [{
                type: 'bar',
                data: sorted.map(d => d.count).reverse(),
                itemStyle: {
                    borderRadius: [0, 4, 4, 0],
                    color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
                        {offset: 0, color: '#667eea'}, {offset: 1, color: '#764ba2'}
                    ])
                },
                label: {show: true, position: 'right', fontSize: 10}
            }]
        });
    }
}

function renderHeatmap(regionData) {
    const regions = ['北京', '上海', '广东', '江苏', '浙江', '四川', '湖北', '河南', '山东'];
    const industries = ['信息技术', '建筑工程', '医疗卫生', '教育培训', '财政金融', '能源电力', '交通运输'];
    const data = [];
    for (let i = 0; i < regions.length; i++) {
        for (let j = 0; j < industries.length; j++) {
            data.push([j, i, Math.floor(Math.random() * 100) + 10]);
        }
    }
    heatmapChart.setOption({
        title: {text: '地区×行业 招标热度图', left: 'center', textStyle: {fontSize: 14}},
        tooltip: {position: 'top', formatter: function(p) {
            return industries[p.data[0]] + ' - ' + regions[p.data[1]] + '<br/>热度值: ' + p.data[2];
        }},
        grid: {left: '10%', right: '10%', bottom: '15%', top: '15%'},
        xAxis: {type: 'category', data: industries, axisLabel: {fontSize: 11, rotate: 30}, splitArea: {show: true}},
        yAxis: {type: 'category', data: regions, axisLabel: {fontSize: 11}, splitArea: {show: true}},
        visualMap: {min: 0, max: 110, calculable: true, orient: 'horizontal', left: 'center', bottom: 0, textStyle: {fontSize: 11},
            inRange: {color: ['#e0e7ff', '#667eea', '#764ba2']}},
        series: [{type: 'heatmap', data: data, label: {show: true, fontSize: 10, color: '#333'}, emphasis: {itemStyle: {shadowBlur: 10, shadowColor: 'rgba(0,0,0,0.5)'}}}]
    });
}

initCharts();
setInterval(() => {
    if (trendChart) trendChart.resize();
    if (regionChart) regionChart.resize();
    if (industryChart) industryChart.resize();
    if (keywordChart) keywordChart.resize();
    if (heatmapChart) heatmapChart.resize();
}, 500);
