let currentPage = 1;
const perPage = 15;

function loadData() {
    const keyword = document.getElementById('filterKeyword').value.trim();
    const region = document.getElementById('filterRegion').value;
    const industry = document.getElementById('filterIndustry').value;
    const startDate = document.getElementById('filterStartDate').value;
    const endDate = document.getElementById('filterEndDate').value;
    const sortBy = document.getElementById('filterSort').value;
    const tbody = document.getElementById('listTableBody');
    tbody.innerHTML = '<tr><td colspan="8" class="empty-cell">正在加载数据...</td></tr>';
    const params = new URLSearchParams({
        keyword: keyword, region: region, industry: industry,
        start_date: startDate, end_date: endDate, sort_by: sortBy,
        page: currentPage, per_page: perPage
    });
    fetch('/api/bidding?' + params.toString()).then(r => r.json()).then(data => {
        if (data.success) {
            renderTable(data.data);
            renderPagination(data.total);
            document.getElementById('listSummary').textContent = 
                `共 ${data.total} 条数据` + (data.from_cache ? ' (来自Redis缓存)' : '');
        } else {
            tbody.innerHTML = '<tr><td colspan="8" class="empty-cell">加载失败</td></tr>';
        }
    }).catch(() => {
        tbody.innerHTML = '<tr><td colspan="8" class="empty-cell">网络错误</td></tr>';
    });
}

function renderTable(data) {
    const tbody = document.getElementById('listTableBody');
    if (!data || data.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="empty-cell">暂无数据，请先到控制台进行采集</td></tr>';
        return;
    }
    const regionMap = {beijing:'北京',shanghai:'上海',guangdong:'广东',jiangsu:'江苏',zhejiang:'浙江',sichuan:'四川',hubei:'湖北',henan:'河南',shandong:'山东',all:'全部'};
    const industryMap = {it:'信息技术',construction:'建筑工程',medical:'医疗卫生',education:'教育培训',finance:'财政金融',energy:'能源电力',transport:'交通运输'};
    let html = '';
    data.forEach((item, idx) => {
        const rowNum = (currentPage - 1) * perPage + idx + 1;
        html += `<tr>
            <td>${rowNum}</td>
            <td class="title-cell"><a href="/detail/${item.id}">${item.title}</a></td>
            <td>${regionMap[item.region] || item.region}</td>
            <td>${industryMap[item.industry] || item.industry}</td>
            <td>${item.publish_date}</td>
            <td>${item.budget}</td>
            <td>${item.source || '-'}</td>
            <td><a href="/detail/${item.id}">查看</a></td>
        </tr>`;
    });
    tbody.innerHTML = html;
}

function renderPagination(total) {
    const totalPages = Math.ceil(total / perPage);
    const el = document.getElementById('pagination');
    if (totalPages <= 1) {
        el.innerHTML = `<span class="page-info">共 ${total} 条</span>`;
        return;
    }
    let html = `<button class="page-btn" onclick="goPage(1)" ${currentPage === 1 ? 'disabled' : ''}>首页</button>`;
    html += `<button class="page-btn" onclick="goPage(${currentPage - 1})" ${currentPage === 1 ? 'disabled' : ''}>上一页</button>`;
    const start = Math.max(1, currentPage - 2);
    const end = Math.min(totalPages, currentPage + 2);
    for (let i = start; i <= end; i++) {
        html += `<button class="page-btn ${i === currentPage ? 'active' : ''}" onclick="goPage(${i})">${i}</button>`;
    }
    html += `<button class="page-btn" onclick="goPage(${currentPage + 1})" ${currentPage === totalPages ? 'disabled' : ''}>下一页</button>`;
    html += `<button class="page-btn" onclick="goPage(${totalPages})" ${currentPage === totalPages ? 'disabled' : ''}>末页</button>`;
    html += `<span class="page-info">第 ${currentPage}/${totalPages} 页，共 ${total} 条</span>`;
    el.innerHTML = html;
}

function goPage(page) {
    currentPage = page;
    loadData();
}

function resetFilter() {
    document.getElementById('filterKeyword').value = '';
    document.getElementById('filterRegion').value = 'all';
    document.getElementById('filterIndustry').value = '';
    document.getElementById('filterStartDate').value = '';
    document.getElementById('filterEndDate').value = '';
    document.getElementById('filterSort').value = 'date';
    currentPage = 1;
    loadData();
}

document.getElementById('filterKeyword').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') { currentPage = 1; loadData(); }
});

loadData();
