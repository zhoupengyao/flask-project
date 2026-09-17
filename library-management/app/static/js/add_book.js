$(document).ready(function() {
    // 作者管理功能
    let authors = [];
    // 如果是编辑模式，从隐藏字段加载已有作者
    var initialAuthors = $('#author').val();
    if (initialAuthors) {
        authors = initialAuthors.split(',').map(function(a) { return a.trim(); }).filter(function(a) { return a; });
        updateAuthorsDisplay();
    }

    $('#addAuthorBtn').click(function() {
        const authorName = $('#authorInput').val().trim();
        if (authorName && !authors.includes(authorName)) {
            authors.push(authorName);
            updateAuthorsDisplay();
            $('#authorInput').val('');
        }
    });

    $('#authorInput').keypress(function(e) {
        if (e.which === 13) {
            e.preventDefault();
            $('#addAuthorBtn').click();
        }
    });

    function updateAuthorsDisplay() {
        const container = $('#authorsContainer');
        container.empty();

        authors.forEach((author, index) => {
            const tag = $('<span class="author-tag"></span>');
            tag.text(author);

            const removeBtn = $('<span class="remove-author"><i class="fas fa-times"></i></span>');
            removeBtn.click(function() {
                authors.splice(index, 1);
                updateAuthorsDisplay();
            });

            tag.append(removeBtn);
            container.append(tag);
        });

        // 更新隐藏的作者字段
        $('#author').val(authors.join(','));
    }

    // 图片预览功能（保持不变）
    $('#bookCover').change(function(e) {
        const file = e.target.files[0];
        const fileLabel = $(this).next('.custom-file-label');

        if (file) {
            // 检查文件类型
            if (!file.type.match('image.*')) {
                alert('请选择图片文件！');
                $(this).val('');
                fileLabel.text('选择封面图片');
                return;
            }

            // 检查文件大小（限制为5MB）
            if (file.size > 5 * 1024 * 1024) {
                alert('图片大小不能超过5MB！');
                $(this).val('');
                fileLabel.text('选择封面图片');
                return;
            }

            const reader = new FileReader();

            reader.onload = function(e) {
                $('#coverPreview')
                    .attr('src', e.target.result)
                    .show()
                    .css({
                        'object-fit': 'cover',
                        'width': '100%',
                        'height': '100%'
                    });
                $('.book-cover-preview i').hide();
            };

            reader.onerror = function() {
                alert('图片读取失败，请重新选择！');
                $(this).val('');
                fileLabel.text('选择封面图片');
                $('#coverPreview').hide();
                $('.book-cover-preview i').show();
            };

            reader.readAsDataURL(file);

            // 更新文件标签显示文件名
            fileLabel.text(file.name);
        } else {
            // 如果没有选择文件，恢复默认状态
            resetCoverPreview();
        }
    });

    // 重置封面预览
    function resetCoverPreview() {
        $('#coverPreview')
            .attr('src', '#')
            .hide()
            .removeAttr('style');
        $('.book-cover-preview i').show();
        $('.custom-file-label').text('选择封面图片');
        $('#bookCover').val('');
    }

    // 表单重置时也重置封面预览
    $('button[type="reset"]').click(function() {
        setTimeout(function() {
            resetCoverPreview();
            authors = [];
            updateAuthorsDisplay();
        }, 100);
    });

    // 拖拽上传功能（保持不变）
    const bookCoverPreview = $('.book-cover-preview')[0];

    $(bookCoverPreview).on('dragover', function(e) {
        e.preventDefault();
        e.stopPropagation();
        $(this).css({
            'border-color': '#3498db',
            'background-color': '#e3f2fd'
        });
    });

    $(bookCoverPreview).on('dragleave', function(e) {
        e.preventDefault();
        e.stopPropagation();
        $(this).css({
            'border-color': '#ddd',
            'background-color': '#f8f9fa'
        });
    });

    $(bookCoverPreview).on('drop', function(e) {
        e.preventDefault();
        e.stopPropagation();
        $(this).css({
            'border-color': '#ddd',
            'background-color': '#f8f9fa'
        });

        const files = e.originalEvent.dataTransfer.files;
        if (files.length > 0) {
            const file = files[0];

            // 模拟文件输入
            const dataTransfer = new DataTransfer();
            dataTransfer.items.add(file);
            $('#bookCover')[0].files = dataTransfer.files;

            // 触发change事件
            $('#bookCover').trigger('change');
        }
    });

    // 点击预览区域也可以选择文件
    $(bookCoverPreview).click(function() {
        $('#bookCover').click();
    });

    // 表单提交 - 重要修改：移除 e.preventDefault()，让表单正常提交
    $('#addBookForm').submit(function(e) {
        // 移除 e.preventDefault()，让表单正常提交到后端

        // 验证必填字段
        if (!validateForm()) {
            e.preventDefault(); // 验证失败时阻止提交
            return;
        }

        // 更新隐藏的作者字段
        $('#author').val(authors.join(','));

        // 显示加载状态
        $('button[type="submit"]').prop('disabled', true).html('<i class="fas fa-spinner fa-spin mr-1"></i> 提交中...');
    });

    // 表单验证
    function validateForm() {
        const title = $('#bookTitle').val().trim();
        const isbn = $('#bookIsbn').val().trim();
        const publisher = $('#bookPublisher').val().trim();
        const category = $('#bookCategory').val();
        const quantity = $('#bookQuantity').val();

        if (!title) {
            showErrorMessage('请输入图书名称');
            $('#bookTitle').focus();
            return false;
        }

        if (authors.length === 0) {
            showErrorMessage('请至少添加一位作者');
            $('#authorInput').focus();
            return false;
        }

        if (!isbn) {
            showErrorMessage('请输入ISBN号');
            $('#bookIsbn').focus();
            return false;
        }

        if (!publisher) {
            showErrorMessage('请输入出版社名称');
            $('#bookPublisher').focus();
            return false;
        }

        if (!category) {
            showErrorMessage('请选择图书分类');
            $('#bookCategory').focus();
            return false;
        }

        if (!quantity || quantity < 1) {
            showErrorMessage('请输入有效的入库数量');
            $('#bookQuantity').focus();
            return false;
        }

        return true;
    }

    // 显示错误消息
    function showErrorMessage(message) {
        // 移除之前可能存在的错误消息
        $('.alert-danger').remove();

        const alert = $(
            '<div class="alert alert-danger alert-dismissible fade show" role="alert">' +
            '<i class="fas fa-exclamation-circle mr-2"></i>' +
            message +
            '<button type="button" class="close" data-dismiss="alert">' +
            '<span>&times;</span>' +
            '</button>' +
            '</div>'
        );

        $('.form-container').prepend(alert);

        // 3秒后自动消失
        setTimeout(function() {
            alert.alert('close');
        }, 3000);
    }

    // 初始化文件选择器文本
    $('.custom-file-label').text('选择封面图片');
});

