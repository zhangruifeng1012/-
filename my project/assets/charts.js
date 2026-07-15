(function() {
  var style = getComputedStyle(document.documentElement);
  var accent = style.getPropertyValue('--accent').trim();
  var accent2 = style.getPropertyValue('--accent2').trim();
  var ink = style.getPropertyValue('--ink').trim();
  var muted = style.getPropertyValue('--muted').trim();
  var rule = style.getPropertyValue('--rule').trim();
  var bg2 = style.getPropertyValue('--bg2').trim();
  var bg = style.getPropertyValue('--bg').trim();

  // --- Chart: severity-pie ---
  var pieChart = echarts.init(document.getElementById('chart-severity-pie'), null, { renderer: 'svg' });
  pieChart.setOption({
    animation: false,
    tooltip: {
      trigger: 'item',
      appendToBody: true,
      formatter: '{b}: {c} ({d}%)'
    },
    legend: {
      bottom: 0,
      itemWidth: 12,
      itemHeight: 12,
      textStyle: { color: muted, fontSize: 13, fontFamily: '"Noto Sans CJK SC", sans-serif' }
    },
    color: ['#d63031', '#e17055', '#fdcb6e', '#b2bec3'],
    series: [{
      type: 'pie',
      radius: ['42%', '70%'],
      center: ['50%', '45%'],
      avoidLabelOverlap: true,
      itemStyle: {
        borderColor: bg,
        borderWidth: 2,
        borderRadius: 4
      },
      label: {
        show: true,
        formatter: '{b}\n{c}',
        color: ink,
        fontSize: 13,
        fontFamily: '"Noto Sans CJK SC", sans-serif',
        lineHeight: 18
      },
      labelLine: {
        lineStyle: { color: rule }
      },
      data: [
        { value: 3, name: 'Critical' },
        { value: 4, name: 'Major' },
        { value: 3, name: 'Medium' },
        { value: 3, name: 'Minor' }
      ]
    }]
  });
  window.addEventListener('resize', function() { pieChart.resize(); });

  // --- Chart: module-bar ---
  var barChart = echarts.init(document.getElementById('chart-module-bar'), null, { renderer: 'svg' });
  barChart.setOption({
    animation: false,
    tooltip: {
      trigger: 'axis',
      appendToBody: true,
      axisPointer: { type: 'shadow' }
    },
    grid: {
      left: 120,
      right: 30,
      top: 16,
      bottom: 24
    },
    xAxis: {
      type: 'value',
      minInterval: 1,
      axisLine: { lineStyle: { color: rule } },
      axisTick: { show: false },
      splitLine: { lineStyle: { color: rule, type: 'dashed' } },
      axisLabel: {
        color: muted,
        fontSize: 12,
        fontFamily: '"Noto Sans CJK SC", sans-serif'
      }
    },
    yAxis: {
      type: 'category',
      data: ['访问控制', '数据分析', '登录认证', '数据采集', '趋势分析', '任务管理', '安全全局', '招标列表', '招标详情', '数据去重'],
      axisLine: { lineStyle: { color: rule } },
      axisTick: { show: false },
      axisLabel: {
        color: ink,
        fontSize: 13,
        fontFamily: '"Noto Sans CJK SC", sans-serif'
      }
    },
    series: [{
      type: 'bar',
      data: [
        { value: 2, itemStyle: { color: '#d63031' } },
        { value: 1, itemStyle: { color: '#fdcb6e' } },
        { value: 2, itemStyle: { color: '#b2bec3' } },
        { value: 1, itemStyle: { color: '#e17055' } },
        { value: 1, itemStyle: { color: '#e17055' } },
        { value: 1, itemStyle: { color: '#e17055' } },
        { value: 1, itemStyle: { color: '#e17055' } },
        { value: 1, itemStyle: { color: '#fdcb6e' } },
        { value: 1, itemStyle: { color: '#fdcb6e' } },
        { value: 1, itemStyle: { color: '#b2bec3' } }
      ],
      barWidth: 20,
      itemStyle: {
        borderRadius: [0, 3, 3, 0]
      },
      label: {
        show: true,
        position: 'right',
        color: muted,
        fontSize: 12,
        fontFamily: '"Noto Sans CJK SC", sans-serif'
      }
    }]
  });
  window.addEventListener('resize', function() { barChart.resize(); });
})();