function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}


$(function () {
    $(".pass_info").submit(function (e) {
        e.preventDefault();

        var params = {};
        $(this).serializeArray().map(function (x) {
            params[x.name] = x.value;
        });
        // 取到两次密码进行判断
        var old_password = params["old_password"];
        var new_password = params["new_password"];
        var new_password2 = params["new_password2"];

        if (old_password == '') {
            alert('请填写密码')
            return;
        } else if (new_password == '') {
            alert('请填写新密码')
            return;
        } else if (new_password.length < 6) {
            alert('密码长度不能少于6位')
            return;
        } else if (new_password != new_password2) {
            alert('两次密码输入不一致')
            return;
        }

        $.ajax({
            url: "/user/pass_info",
            type: "post",
            contentType: "application/json",
            headers: {
                "X-CSRFToken": getCookie("csrf_token")
            },
            data: JSON.stringify(params),
            success: function (resp) {
                if (resp.errno == "0") {
                    // 修改成功
                    alert("修改成功")
                    window.location.reload()
                } else {
                    alert(resp.errmsg)
                }
            }
        })
    })
})