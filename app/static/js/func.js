        function sw() {
            var value;
            var isAuto = document.getElementsByName('Type');
            for (var i = 0; i < isAuto.length; i++) {
                if (isAuto[i].checked == true) {
                    value = isAuto[i].value;
                    if (value == "custom")
                        document.getElementById(value).style.display = "";
                    else
                        document.getElementById("custom").style.display = "none";
                }
            }
            var tables = document.getElementsByTagName("table");
            for (var i = 0; i < tables.length; i++) {
                tables[i].style.display = "none";
            }
            document.getElementById(value).style.display = "";
        }

        //控制新加字段的显示
        $(document).ready(function () {
            $('input[type=radio][name=func]').change(function () {
                if (this.value == 'custom') {
                    document.getElementById("custom").style.display = "";
                } else {
                    document.getElementById("custom").style.display = "none";
                }
            });
        });


        $(document).ready(function () {
            $('input[type=radio][name=func]').change(function () {
                if (this.value == 'temp') {
                    //document.getElementById("form1").style.display = "none";
                    document.getElementById("temp").style.display = "";
                } else {
                    //document.getElementById("form1").style.display = "";
                    document.getElementById("temp").style.display = "none";
                }
            });
        });
        $(document).ready(function () {
            $('input[type=radio][name=func]').change(function () {
                if (this.value == 'default') {
                    document.getElementById("form1").style.display = "none";
                    document.getElementById("default").style.display = "";
                } else {
                    document.getElementById("form1").style.display = "";
                    document.getElementById("default").style.display = "none";
                }
            });
        });

        $(document).ready(function () {
            $('input[type=radio][name=Type]').click(function () {
                document.getElementById("select").removeAttribute("disabled");
            });
        });



        function display() {
			document.getElementById("box").style.display = "block";
		}
		function disappear() {
			document.getElementById("box").style.display = "none";
		}

        //产生随机数函数
        function RndNum(n){

            var rnd="";
            for(var i=0;i<n;i++)
                rnd+=Math.floor(Math.random()*10);
            return rnd;
        }
        function temp(){
            //得到你的from
            var form = document.forms['custom_form'];
            //在这里手工指定提交给哪个ACTION
            form.action = '/new2';
            //执行SUBMIT
            form.submit();
        }

        function CheckUrl()
        {
            var str=$("input[id='url']").val()
            var Expression=/http(s)?:\/\/([\w-]+\.)+[\w-]+(\/[\w- .\/?%&=]*)?/;
            var objExp=new RegExp(Expression);

            if(objExp.test(str) != true)
            {

                alert("网址格式不正确！请重新输入必填：协议+域名");
                return false;
            }
        }

        function gradeChange(value) {
            if(value == "two")
            {
                document.getElementById("page").style.display =""
                document.getElementById("box2").style.display = "";
                document.getElementById("box3").style.display = "none";
            }

            else
            {
                document.getElementById("box3").style.display = "";
                document.getElementById("page").style.display ="none"
                document.getElementById("box2").style.display = "none";
            }
        }
    </script>