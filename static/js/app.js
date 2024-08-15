// static/js/app.js

// 获取笔记列表
function fetchNotes() {
    var limit = document.getElementById('notes-limit').value;
    fetch('/notes?limit=' + limit)
        .then(response => response.json())
        .then(data => {
            const notesList = document.getElementById('notes-list');
            notesList.innerHTML = ''; // 清空列表
            data.forEach(note => {
                const listItem = document.createElement('li');
                listItem.textContent = `时间: ${note.time}, 内容:${note.contact}`;
                notesList.appendChild(listItem);
            });
        })
        .catch(error => console.error('Error:', error));
}

// 页面加载时获取笔记列表
document.addEventListener('DOMContentLoaded', fetchNotes);

// 添加笔记
document.getElementById('add-note-form').addEventListener('submit', function(event) {
    event.preventDefault();
    const newContact = document.getElementById('contact').value;
    
    fetch('/notes', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ contact: newContact })
    })
    .then(response => response.json())
    .then(data => {
        alert('笔记添加成功！');
        fetchNotes(); // 更新笔记列表
        document.getElementById('contact').value = ''; // 清除文本框内容
    })
    .catch(error => console.error('Error:', error));
});


//导出笔记
document.addEventListener('DOMContentLoaded', function() {
    const exportForm = document.getElementById('export-notes-form');
    
    exportForm.addEventListener('submit', function(event) {
        event.preventDefault(); // 阻止表单默认提交行为

        const startDate = document.getElementById('start-date').value;
        const endDate = document.getElementById('end-date').value;

        // 发送POST请求到导出路由
        fetch('/export-notes', {
            method: 'POST', // 修改为POST请求
            headers: {
                'Content-Type': 'application/json',
                // 如果需要的话，可以添加更多的头信息，比如认证信息
            },
            body: JSON.stringify({ // 将数据作为JSON字符串发送
                'start-date': startDate,
                'end-date': endDate
            })
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
            downloadLink.download = `notes_${startDate}_to_${endDate}.csv`;
            document.body.appendChild(downloadLink);
            downloadLink.click();
            document.body.removeChild(downloadLink);
        })
        .catch(error => {
            console.error('导出错误:', error);
            alert('导出错误，请稍后再试。');
        });
    });
});
