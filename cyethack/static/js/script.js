let currentHost = '';
let allProcesses = [];
let filteredProcesses = [];
let systemData = {};
let expandedProcesses = {};

const API_ENDPOINTS = {
    hosts: '/api/hosts/',
    processTree: '/api/hosts/{host_id}/processes/latest/', 
    systemInfo: '/api/hosts/{host_id}/system/latest/',    
    systemStatus: '/api/status/',                          
    submitData: '/api/submit/'                              
};

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

async function initializeApp() {
    try {
        await loadHosts();
        await updateSystemStatus();
        setupEventListeners();
        setInterval(updateSystemStatus, 30000);
        showSystemDetails();
        
    } catch (error) {
        console.error('Failed to initialize app:', error);
        showError('Failed to initialize application');
    }
}
// Search Bar logic
function setupEventListeners() {
    const searchInput = document.getElementById('searchInput');
    let searchTimeout;
    searchInput.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            filterProcesses();
        }, 300);
    });
    
    const modal = document.getElementById('processModal');
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            closeModal();
        }
    });
}

async function loadHosts() {
    try {
        const response = await fetch(API_ENDPOINTS.hosts);
        if (!response.ok) throw new Error('Failed to fetch hosts');
        
        const hosts = await response.json();
        const hostSelect = document.getElementById('hostSelect');
        const hostList = document.getElementById('hostList');
        hostSelect.innerHTML = '<option value="">Select a host...</option>';
        hostList.innerHTML = '';
        // Dropdown for host
        hosts.forEach(host => {
            const option = document.createElement('option');
            option.value = host.hostname;
            option.textContent = `${host.hostname} (${host.ip_address || 'Unknown IP'})`;
            hostSelect.appendChild(option);
            const hostItem = document.createElement('div');
            hostItem.className = 'host-item';
            hostItem.textContent = host.hostname;
            hostItem.onclick = () => selectHost(host.hostname);
            hostList.appendChild(hostItem);
        });
        
        // By default select first host as host
        if (hosts.length > 0) {
            selectHost(hosts[0].hostname);
        }
        
    } catch (error) {
        console.error('Error loading hosts:', error);
        showError('Failed to load hosts');
    }
}

function selectHost(hostname) {
    currentHost = hostname;
    document.getElementById('hostSelect').value = hostname;
    document.querySelectorAll('.host-item').forEach(item => {
        item.classList.remove('active');
        if (item.textContent === hostname) {
            item.classList.add('active');
        }
    });
    loadHostData();
}

async function loadHostData() {
    if (!currentHost) return;
    
    try {
        // Load both system and process data
        await Promise.all([
            loadSystemData(),
            loadProcessData()
        ]);
        
    } catch (error) {
        console.error('Error loading host data:', error);
        showError('Failed to load host data');
    }
}

async function loadSystemData() {
    if (!currentHost) return;
    
    try {
        const hostId = await getHostId(currentHost);
        if (!hostId) {
            console.error('Host ID not found for:', currentHost);
            return;
        }
        
        const response = await fetch(API_ENDPOINTS.systemInfo.replace('{host_id}', hostId));
        
        systemData = await response.json();
        renderSystemInfo();
        
    } catch (error) {
        console.error('Error loading system data:', error);
        showError('Failed to load system data');
    }
}

function renderSystemInfo() {
    const systemInfoTable = document.getElementById('systemInfoTable');
    
    if (!systemData || Object.keys(systemData).length === 0) {
        systemInfoTable.innerHTML = '<div class="loading"><p>No system data available</p></div>';
        return;
    }
    
    // Details for system 
    const systemInfo = [
        { label: 'Name', value: systemData.hostname || 'Unknown' },
        { label: 'Operating System', value: systemData.operating_system || 'Unknown' },
        { label: 'Processor', value: systemData.processor || 'Unknown' },
        { label: 'Number of Cores', value: systemData.processor_cores || 'Unknown' },       
        { label: 'Number of Threads', value: systemData.processor_threads || 'Unknown' },  
        { label: 'RAM (GB)', value: systemData.ram_total_gb || 'Unknown' },               
        { label: 'Used RAM (GB)', value: systemData.ram_used_gb || 'Unknown' },           
        { label: 'Available RAM (GB)', value: systemData.ram_available_gb || 'Unknown' }, 
        { label: 'Storage Free (GB)', value: systemData.storage_free_gb || 'Unknown' },    
        { label: 'Storage Total (GB)', value: systemData.storage_total_gb || 'Unknown' },  
        { label: 'Storage Used (GB)', value: systemData.storage_used_gb || 'Unknown' },
        { label: 'Last Updated', value: systemData.timestamp ? new Date(systemData.timestamp).toLocaleString() : 'Unknown' }
    ];
        
    systemInfoTable.innerHTML = systemInfo.map(info => `
        <div class="system-info-row">
            <div class="system-info-label">${info.label}</div>
            <div class="system-info-value">${info.value}</div>
        </div>
    `).join('');
}

// Load process details
async function loadProcessData() {
    if (!currentHost) return;
    
    try {
        const hostId = await getHostId(currentHost);
        if (!hostId) {
            console.error('Host ID not found for:', currentHost);
            return;
        }
        
        const response = await fetch(API_ENDPOINTS.processTree.replace('{host_id}', hostId));
        if (!response.ok) {
            if (response.status === 404) {
                allProcesses = [];
                filteredProcesses = [];
                renderProcessTable();
                return;
            }
            throw new Error('Failed to fetch process data');
        }
        
        const data = await response.json();
        allProcesses = data.processes || [];
        filteredProcesses = [...allProcesses];
        renderProcessTable();
        
    } catch (error) {
        console.error('Error loading process data:', error);
        showError('Failed to load process data');
        allProcesses = [];
        filteredProcesses = [];
        renderProcessTable();
    }
}

// Process Table
function renderProcessTable() {
    const processTableBody = document.getElementById('processTableBody');
    if (!processTableBody) return;

    if (!filteredProcesses || filteredProcesses.length === 0) {
        processTableBody.innerHTML = allProcesses.length === 0
            ? `<tr><td colspan="8" class="no-data"><i class="fas fa-info-circle"></i><p>No process data</p><small>Make sure the monitoring agent is running</small></td></tr>`
            : `<tr><td colspan="8" class="no-data"><i class="fas fa-search"></i><p>No processes match your search criteria</p></td></tr>`;
        return;
    }

    const processMap = new Map();
    const rootProcesses = [];

    filteredProcesses.forEach(proc => {
        processMap.set(proc.pid, {
            ...proc,
            children: [],
            expanded: !!expandedProcesses[proc.pid]
        });
    });

    filteredProcesses.forEach(proc => {
        if (proc.parent_pid && processMap.has(proc.parent_pid)) {
            processMap.get(proc.parent_pid).children.push(processMap.get(proc.pid));
        } else {
            rootProcesses.push(processMap.get(proc.pid));
        }
    });

    processTableBody.innerHTML = '';
    rootProcesses.forEach(proc => {
        renderProcessHierarchy(proc, 0, processTableBody);
    });
}

function renderProcessHierarchy(process, level, container) {
    const row = createProcessRow(process, level);
    row.setAttribute('data-pid', process.pid);
    row.setAttribute('data-level', level);
    container.appendChild(row);

    if (process.expanded && process.children && process.children.length > 0) {
        process.children.forEach(child => {
            renderProcessHierarchy(child, level + 1, container);
        });
    }
}

function toggleProcessExpansion(pid) {
    expandedProcesses[pid] = !expandedProcesses[pid];
    renderProcessTable();
}
function createProcessRow(process, level) {
    const row = document.createElement('tr');
    row.className = 'process-row';
    if (level > 0) row.classList.add('child');
    
    const hasChildren = process.children && process.children.length > 0;
    const indent = level * 20;
    const processName = process.name || 'Unknown';
    const memoryMB = process.memory_mb !== null && process.memory_mb !== undefined ? parseFloat(process.memory_mb) : 0;
    const cpuPercent = process.cpu_percent !== null && process.cpu_percent !== undefined ? parseFloat(process.cpu_percent) : 0;
    const parentPID = process.parent_pid || '-';
    const status = process.status || 'running';
    const username = process.username || 'Unknown';
    const commandLine = process.command_line || '';
    const createdTime = process.created_time || 'Unknown';
    const truncatedCommand = commandLine.length > 50 ? commandLine.substring(0, 50) + '...' : commandLine;
    let formattedTime = 'Unknown';
    if (createdTime !== 'Unknown' && createdTime) {
        try {
            formattedTime = new Date(createdTime).toLocaleString();
        } catch (e) {
            formattedTime = 'Invalid Date';
        }
    }
    const toggleIcon = process.expanded ? '▼' : '▶';

    row.innerHTML = `
        <td>
            <div class="process-name" style="padding-left: ${indent}px;">
                ${hasChildren ? `<span class="process-toggle" onclick="toggleProcessExpansion(${process.pid})">${toggleIcon}</span>` : '<span class="process-toggle-placeholder"></span>'}
                <span onclick="showProcessDetails(${JSON.stringify(process).replace(/"/g, '&quot;')})">${processName}</span>
            </div>
        </td>
        <td class="text-right">${memoryMB > 0 ? memoryMB.toFixed(2) : '0.00'}</td>
        <td class="text-right">${cpuPercent > 0 ? cpuPercent.toFixed(1) : '0.0'}</td>
        <td class="text-center">${parentPID}</td>
        <td class="text-center">
            <span class="status-badge ${status.toLowerCase()}">${status}</span>
        </td>
        <td>${username}</td>
        <td class="command-line" title="${commandLine}">${truncatedCommand}</td>
        <td class="text-center">${formattedTime}</td>
    `;
    
    return row;
}

// Filter process logic
function filterProcesses() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    
    if (!searchTerm.trim()) {
        filteredProcesses = [...allProcesses];
    } else {
        filteredProcesses = allProcesses.filter(process => 
            process.name.toLowerCase().includes(searchTerm) ||
            process.pid.toString().includes(searchTerm) ||
            (process.command_line && process.command_line.toLowerCase().includes(searchTerm))
        );
    }
    renderProcessTable();
}

function showProcessDetails(process) {
    const modal = document.getElementById('processModal');
    const detailsContainer = document.getElementById('processDetails');
    
    detailsContainer.innerHTML = `
        <div class="detail-row">
            <span class="detail-label">Process Name:</span>
            <span class="detail-value">${process.name}</span>
        </div>
        <div class="detail-row">
            <span class="detail-label">PID:</span>
            <span class="detail-value">${process.pid}</span>
        </div>
        <div class="detail-row">
            <span class="detail-label">Parent PID:</span>
            <span class="detail-value">${process.parent_pid || 'None (Root)'}</span>
        </div>
        <div class="detail-row">
            <span class="detail-label">Username:</span>
            <span class="detail-value">${process.username || 'Unknown'}</span>
        </div>
        <div class="detail-row">
            <span class="detail-label">Status:</span>
            <span class="detail-value">${process.status || 'Running'}</span>
        </div>
        <div class="detail-row">
            <span class="detail-label">CPU Usage:</span>
            <span class="detail-value">${process.cpu_percent.toFixed(2)}%</span>
        </div>
        <div class="detail-row">
            <span class="detail-label">Memory Usage:</span>
            <span class="detail-value">${process.memory_mb.toFixed(2)} MB (${process.memory_percent.toFixed(2)}%)</span>
        </div>
        <div class="detail-row">
            <span class="detail-label">Created Time:</span>
            <span class="detail-value">${process.created_time || 'Unknown'}</span>
        </div>
        <div class="detail-row">
            <span class="detail-label">Command Line:</span>
            <span class="detail-value">${process.command_line || 'Not available'}</span>
        </div>
    `;
    
    modal.style.display = 'block';
}

function closeModal() {
    const modal = document.getElementById('processModal');
    modal.style.display = 'none';
}

function showSystemDetails() {
    document.getElementById('systemDetails').style.display = 'block';
    document.getElementById('processDetails').style.display = 'none';
    
    document.getElementById('systemTab').classList.add('active');
    document.getElementById('processTab').classList.remove('active');
    
    if (currentHost) {
        loadSystemData();
    }
}

function showProcessDetails() {
    document.getElementById('systemDetails').style.display = 'none';
    document.getElementById('processDetails').style.display = 'block';
    
    document.getElementById('systemTab').classList.remove('active');
    document.getElementById('processTab').classList.add('active');
    
    if (currentHost) {
        loadProcessData();
    }
}


async function updateSystemStatus() {
    try {
        const response = await fetch(API_ENDPOINTS.systemStatus);
        if (!response.ok) throw new Error('Failed to fetch system status');
        
        const status = await response.json();
        
        const statusIndicator = document.getElementById('statusIndicator');
        const statusText = document.getElementById('statusText');
        
        if (status.status === 'online') {
            statusIndicator.className = 'status-indicator online';
            statusText.textContent = 'Online';
        } else {
            statusIndicator.className = 'status-indicator offline';
            statusText.textContent = 'Offline';
        }
        
    } catch (error) {
        console.error('Error updating system status:', error);
        const statusIndicator = document.getElementById('statusIndicator');
        const statusText = document.getElementById('statusText');
        
        statusIndicator.className = 'status-indicator offline';
        statusText.textContent = 'Connection Error';
    }
}

function showError(message) {
    console.error(message);
    alert(message);
}

// helper
async function getHostId(hostname) {
    try {
        const response = await fetch(API_ENDPOINTS.hosts);
        if (!response.ok) throw new Error('Failed to fetch hosts');
        
        const hosts = await response.json();
        const host = hosts.find(h => h.hostname === hostname);
        return host ? host.id : null;
    } catch (error) {
        console.error('Error getting host ID:', error);
        return null;
    }
}
