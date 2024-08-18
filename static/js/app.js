// 获取笔记列表
function fetchNotes() {
    var limit = document.getElementById('notes-limit').value;
    var type = document.getElementById('notes-type').value; // 获取笔记类型
    // 检查是否选择了“笔记和杂物堆”选项
    var queryType = type === 'all' ? '' : `&type=${type}`;
    fetch(`/notes?limit=${limit}${queryType}`)
        .then(response => response.json())
        .then(data => {
            const notesList = document.getElementById('notes-list');
            notesList.innerHTML = ''; // 清空列表
            data.forEach(note => {
                const listItem = document.createElement('li');
                // 使用.replace()方法将文本中的\n替换为<br>
                const contentWithBreaks = note.contact.replace(/\n/g, '<br>');
                listItem.innerHTML = `时间: ${note.time}, 类型:${note.type === 0 ? '笔记' : '杂物堆'}<br>${contentWithBreaks}`;
                notesList.appendChild(listItem);
            });
        })
        .catch(error => console.error('Error:', error));
}


// 页面加载时获取笔记列表
document.addEventListener('DOMContentLoaded', fetchNotes);

// 为笔记类型选择框添加事件监听器
document.getElementById('notes-type').addEventListener('change', function() {
    fetchNotes(); // 当类型改变时重新获取笔记列表
});

// 添加笔记
document.getElementById('add-note-form').addEventListener('submit', function(event) {
    event.preventDefault();
    const newContact = document.getElementById('contact').value;
    const noteType = document.getElementById('note-type').value; // 获取笔记类型
    fetch('/notes', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            contact: newContact,
            type: noteType // 发送笔记类型
        })
    })
    .then(response => response.json())
    .then(data => {
        alert('笔记添加成功！');
        fetchNotes(); // 更新笔记列表
        document.getElementById('contact').value = ''; // 清除文本框内容
    })
    .catch(error => console.error('Error:', error));
});

// 导出笔记
document.getElementById('export-notes-form').addEventListener('submit', function(event) {
    event.preventDefault();
    const startDate = document.getElementById('start-date').value;
    const endDate = document.getElementById('end-date').value;
    const exportType = document.getElementById('export-type').value;
    // 检查是否选择了“笔记和杂物堆”选项
    let bodyData = {
        'start-date': startDate,
        'end-date': endDate
    };
    if (exportType !== 'all') {
        bodyData.type = exportType;
    }
    fetch('/export-notes', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(bodyData)
    })
    .then(response => {
        if (response.ok) {
            return response.blob(); // 获取文件流
        } else {
            throw new Error('导出失败');
        }
    })
    .then(blob => {
        // 创建一个链接元素用于下载
        const downloadLink = document.createElement('a');
        downloadLink.href = window.URL.createObjectURL(blob);
        downloadLink.download = `notes_${startDate}_to_${endDate}_type_${exportType}.csv`; // 设置下载文件名
        document.body.appendChild(downloadLink);
        downloadLink.click();
        document.body.removeChild(downloadLink);
    })
    .catch(error => {
        console.error('导出错误:', error);
        alert('导出错误，请稍后再试。');
    });
});