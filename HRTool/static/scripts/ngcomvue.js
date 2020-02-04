// var BASEURL = "http://localhost/ngcomportalv2/index.php/api/v1/";
var BASEURL = window.BASE_URL;
let BASEROOT = $('#rootbase').val();
var username = $('#usr').val();
//console.log(BASEROOT + 'css/print.css');
var ngcom = new Vue({
    el: "#ngcomportal",
    data: {
        showChequeno: false,
        paymenthistory: [],
        latesthistory: [],
        userreceipt: {},
        cardinfo: {},
        totalamount: "",
        subperiod: 1,
        countries: ["Afghanistan", "Albania", "Algeria", "American Samoa", "Andorra", "Angola", "Anguilla", "Antarctica", "Antigua and Barbuda", "Argentina", "Armenia", "Aruba", "Australia", "Austria", "Azerbaijan", "Bahamas", "Bahrain", "Bangladesh", "Barbados", "Belarus", "Belgium", "Belize", "Benin", "Bermuda", "Bhutan", "Bolivia", "Bosnia and Herzegowina", "Botswana", "Bouvet Island", "Brazil", "British Indian Ocean Territory", "Brunei Darussalam", "Bulgaria", "Burkina Faso", "Burundi", "Cambodia", "Cameroon", "Canada", "Cape Verde", "Cayman Islands", "Central African Republic", "Chad", "Chile", "China", "Christmas Island", "Cocos (Keeling) Islands", "Colombia", "Comoros", "Congo", "Congo, the Democratic Republic of the", "Cook Islands", "Costa Rica", "Cote d'Ivoire", "Croatia (Hrvatska)", "Cuba", "Cyprus", "Czech Republic", "Denmark", "Djibouti", "Dominica", "Dominican Republic", "East Timor", "Ecuador", "Egypt", "El Salvador", "Equatorial Guinea", "Eritrea", "Estonia", "Ethiopia", "Falkland Islands (Malvinas)", "Faroe Islands", "Fiji", "Finland", "France", "France Metropolitan", "French Guiana", "French Polynesia", "French Southern Territories", "Gabon", "Gambia", "Georgia", "Germany", "Ghana", "Gibraltar", "Greece", "Greenland", "Grenada", "Guadeloupe", "Guam", "Guatemala", "Guinea", "Guinea-Bissau", "Guyana", "Haiti", "Heard and Mc Donald Islands", "Holy See (Vatican City State)", "Honduras", "Hong Kong", "Hungary", "Iceland", "India", "Indonesia", "Iran (Islamic Republic of)", "Iraq", "Ireland", "Israel", "Italy", "Jamaica", "Japan", "Jordan", "Kazakhstan", "Kenya", "Kiribati", "Korea, Democratic People's Republic of", "Korea, Republic of", "Kuwait", "Kyrgyzstan", "Lao, People's Democratic Republic", "Latvia", "Lebanon", "Lesotho", "Liberia", "Libyan Arab Jamahiriya", "Liechtenstein", "Lithuania", "Luxembourg", "Macau", "Macedonia, The Former Yugoslav Republic of", "Madagascar", "Malawi", "Malaysia", "Maldives", "Mali", "Malta", "Marshall Islands", "Martinique", "Mauritania", "Mauritius", "Mayotte", "Mexico", "Micronesia, Federated States of", "Moldova, Republic of", "Monaco", "Mongolia", "Montserrat", "Morocco", "Mozambique", "Myanmar", "Namibia", "Nauru", "Nepal", "Netherlands", "Netherlands Antilles", "New Caledonia", "New Zealand", "Nicaragua", "Niger", "Nigeria", "Niue", "Norfolk Island", "Northern Mariana Islands", "Norway", "Oman", "Pakistan", "Palau", "Panama", "Papua New Guinea", "Paraguay", "Peru", "Philippines", "Pitcairn", "Poland", "Portugal", "Puerto Rico", "Qatar", "Reunion", "Romania", "Russian Federation", "Rwanda", "Saint Kitts and Nevis", "Saint Lucia", "Saint Vincent and the Grenadines", "Samoa", "San Marino", "Sao Tome and Principe", "Saudi Arabia", "Senegal", "Seychelles", "Sierra Leone", "Singapore", "Slovakia (Slovak Republic)", "Slovenia", "Solomon Islands", "Somalia", "South Africa", "South Georgia and the South Sandwich Islands", "Spain", "Sri Lanka", "St. Helena", "St. Pierre and Miquelon", "Sudan", "Suriname", "Svalbard and Jan Mayen Islands", "Swaziland", "Sweden", "Switzerland", "Syrian Arab Republic", "Taiwan, Province of China", "Tajikistan", "Tanzania, United Republic of", "Thailand", "Togo", "Tokelau", "Tonga", "Trinidad and Tobago", "Tunisia", "Turkey", "Turkmenistan", "Turks and Caicos Islands", "Tuvalu", "Uganda", "Ukraine", "United Arab Emirates", "United Kingdom", "United States", "United States Minor Outlying Islands", "Uruguay", "Uzbekistan", "Vanuatu", "Venezuela", "Vietnam", "Virgin Islands (British)", "Virgin Islands (U.S.)", "Wallis and Futuna Islands", "Western Sahara", "Yemen", "Yugoslavia", "Zambia", "Zimbabwe"],
        customer: {
            department: "Please Select a Department",
            subject: "",
            message: ""
        },
        isadmin: "",

        profile: {},
        password: {
            crtpswd: "",
            newpswd: "",
            retypepswd: "",
        },
        userlist: [],
        userPayment: [],
        searchusers: ""


    },
    methods: {
        PrintElem(elem)
        {
            var mywindow = window.open('', 'PRINT', 'height=400,width=600');

            mywindow.document.write('<html><head><title>' + document.title + '</title>');
            mywindow.document.write('<link rel="stylesheet" href="' + BASEROOT + 'css/print.css" type="text/css" />');

            mywindow.document.write('</head><body >');
            mywindow.document.write('<h1>' + document.title + '</h1>');
            mywindow.document.write(document.getElementById(elem).innerHTML);
            mywindow.document.write('</body></html>');

            mywindow.document.close(); // necessary for IE >= 10
            mywindow.focus();
            setTimeout(function () {
                mywindow.print();
                mywindow.close();
            }, 1000);

            return true;
        },
        fetchPaymentHistory: function () {
            $.blockUI({
                message: '<h3>Please Wait...</h3>',
                css: {
                    backgroundColor: '#E5EFF1', color: 'black',
                    padding: "10px", borderRadius: "5px", border: "0", zIndex: 99999999999999
                }
            });
            $.ajax({
                type: 'get',
                url: BASEURL + "paymenthistory/fetch?username=" + username,
                success: function (response) {
                    // //console.log(response.list)
                    ngcom.paymenthistory = response.list;
                    $.unblockUI();
                    $('#historyModal').modal('show')
                    //console.log(ngcom.paymenthistory, "PAYMENT HISTORY")
                    ngcom.values = response.list;
                    // //console.log(ngcom.values)

                }
            });
        },
        fetchUserPaymentHistory: function (username_id) {
            $.blockUI({
                message: '<h3>Please Wait...</h3>',
                css: {
                    backgroundColor: '#E5EFF1', color: 'black',
                    padding: "10px", borderRadius: "5px", border: "0", zIndex: 99999999999
                }
            });
            $.ajax({
                type: 'get',
                url: BASEURL + "paymenthistory/fetch?username=" + username_id,
                success: function (response) {
                    //console.log(response.list)
                    ngcom.userPayment = response.list;
                    $.unblockUI();
                    $('#userPaymentModal').modal('show')
                    //console.log(ngcom.userPayment, "USER PAYMENTS")


                }
            });
        },
        fetchLatestHistory() {
            $.blockUI({
                message: '<h3>Please Wait...</h3>',
                css: {
                    backgroundColor: '#E5EFF1', color: 'black',
                    padding: "10px", borderRadius: "5px", border: "0"
                }
            });
            $.ajax({
                type: 'get',
                url: BASEURL + "paymenthistory/fetchten?username=" + username,
                success: function (response) {


                    //console.log(response.list)
                    var vat = response.list.unitprice * 0.05;
                    $.unblockUI();
                    $('#overviewModal').modal('show')
                    ngcom.latesthistory = response.list;
                    //console.log(ngcom.latesthistory)

                }
            });
        },
        addCommas(nStr) {
            nStr += '';
            var x = nStr.split('.');
            var x1 = x[0];
            var x2 = x.length > 1 ? '.' + x[1] : '';
            var rgx = /(\d+)(\d{3})/;
            while (rgx.test(x1)) {
                x1 = x1.replace(rgx, '$1' + ',' + '$2');
            }
            return x1 + x2;
        },
        changeManualPaymentService() {
            var user = $('input[name=manualpaymentuser]').val();
            let usersArray = ngcom.userlist;
            //console.log('It id running')
            usersArray.forEach(function (object) {
                if (object.username === user) {
                    $('input[name=manualpaymentservice]').val(object.servicename);
                    $('input[name=manualpaymentlastexpiration]').val(object.expiration.split(' ')[0]);
                }
            })


            // //console.log(usersArray,"Username")
            // //console.log(user,"Username")
            // //console.log(userObject,"User Object")
            $('input[name=manualpaymentservice]').val();
        },
        convertDate(date) {
            if (date === null) {
                return " "
            } else {
                var day = new Date(date);
                return day.toDateString()
            }
        },
        fetchUsers() {
            //console.log(username);
            $.ajax({
                type: 'GET',
                url: BASEURL + "users/fetusers?username=" + username,
                success: function (response) {
                    //console.log(response, );
                    ngcom.userlist = response;
                }
            })
        },
        changePaymentOption() {
            let Payment_Option = $('select[name=manualpaymentmethod]').val();

            if (Payment_Option === "cheque") {
                ngcom.showChequeno = true;
            } else {
                ngcom.showChequeno = false;
            }
        },
        addManualHistory() {
            let username = $('input[name=manualpaymentuser]').val();
            let payment_method = $('select[name=manualpaymentmethod]').val();
            let qty = $('select[name=manualpaymentqty]').val();
            // let expiration = $('input[name=manualexpirationdate]').val();
            let orderdate = $('input[name=manualpaymentoderdate]').val();
            let loading = $('#manualloading')
            let cheque = $('input[name=manualpaymentcheque]') === undefined ? $('input[name=manualpaymentcheque]').val() : "";

            let data = {username, qty, orderdate, payment_method, cheque};
            if ((username === "") || (payment_method === "") || (qty === "") || (orderdate === "")) {
                alert('Please Complete all fields')
            } else {
                $('#manualhistory').attr('disabled', true);
                loading.css('display', 'inline')
                // //console.log(data)
                $.ajax({
                    type: 'POST',
                    data,
                    url: BASEURL + "payments/createPayment",
                    success: function (response) {
                        //console.log(response);
                        if(response.action){
                            window.location.reload();
                        }
                        if (response.message) {
                            alert(response.message);
                            loading.css('display', 'none')
                            $('#enterpaymentmanually').modal('hide');
                            window.location.reload();
                        } else {
                            alert('An Error Occurred');
                            loading.addClass('hidden');
                        }
                    }
                })
            }
        },
        capitalize(delimeter, string){
            let newArr = string ? string.split(delimeter) :[];
   for(var i = 0 ; i < newArr.length ; i++){
    newArr[i] = newArr[i].charAt(0).toUpperCase() + newArr[i].substr(1);
}
console.log(newArr);
    return newArr.join(" ");
        },
        fetchCardInfo() {
            $.ajax({
                type: 'get',
                url: BASEURL + "cardpayment/fetch?username=" + username,
                success: function (response) {
//                    console.log(response);
                    ngcom.cardinfo = response;
                    ngcom.values = response.list;
                    //console.log(ngcom.values)
                    ngcom.totalamount = ngcom.cardinfo.rm_services.unitprice * parseInt(ngcom.subperiod);
                    //for Profile
                    ngcom.profile = response.rm_users;
                    ngcom.isadmin = parseInt(response.portaluser.isadmin);
                    //console.log(ngcom.isadmin);
                    ;
                }
            })
        },
        changeTotalAmount() {
            ngcom.totalamount = ngcom.cardinfo.rm_services.unitprice * parseInt(ngcom.subperiod);
        },
        showUpdatePassword(username) {
            $('#updateusersportalpassword').modal('show');

            $('input[name=updateuserpasswordusername]').val(username);
        },
        updateUserPassword() {
            let username = $('input[name=updateuserpasswordusername]').val();
            let password = $('input[name=updateuserpassword]').val();
                        let loading = $('#manualloading')

            let data = {
                username, password
            }
            if (password !== "") {
                                loading.css('display', 'inline')

                $.ajax({
                    type: 'post',
                    url: BASEURL + 'users/updateUserPassword',
                    data,
                    success: function (response) {
                        //console.log(response)
                                                    loading.css('display', 'none')

                        alert(response.message)
                        if(response.status === true){
                            window.location.reload();
                        }
                    },
                    error: function (error) {
                        //console.log(error)
                    }
                })
            }else{
                                            loading.css('display', 'none')

                alert('Please enter a New Password for user')
            }

        },
        changePassword() {
            var oldpassword = ngcom.cardinfo.portaluser.password;
            //console.log(oldpassword)
            if ((ngcom.password.newpswd === "") && (ngcom.password.retypepswd == "") || (ngcom.password.crtpswd === "")) {

                $('input[name=new-password]').css('border-color', 'red')
                $('input[name=retype-password]').css('border-color', 'red')
                $('input[name=current-password]').css('border-color', 'red')
                alert("PLEASE COMPLETE ALL FIELDS ")

            } else if (ngcom.password.newpswd != ngcom.password.retypepswd) {
                $('input[name=new-password]').css('border-color', 'red')
                $('input[name=retype-password]').css('border-color', 'red')
                $('input[name=current-password]').css('border-color', '#ced4da')
                alert("PLEASE ENTER THE SAME new password ")
            } else {
                $('input[name=new-password]').css('border-color', '#ced4da')
                $('input[name=retype-password]').css('border-color', '#ced4da')
                $('input[name=current-password]').css('border-color', '#ced4da')

                var {retypepswd, crtpswd} = ngcom.password
                var freshPassword = {
                    oldpassword: crtpswd,
                    password: oldpassword,
                    newpassword: retypepswd,
                    username: username
                }
                $.ajax({
                    type: 'post',
                    url: BASEURL + 'cardpayment/updatepassword',
                    data: freshPassword,
                    success: function (response) {
                        if (response === 'inccorect-old-password') {
                            $('input[name=current-password]').css('border-color', 'red');
                            $('input[name=current-password]').focus();
                            alert("Current Password Does not Match");
                        } else if (response === 'unchanged') {
                            alert('Error in Changing Password')
                        } else {
                            alert("Password Changed Successfully")

                        }
                    }
                })
            }
        },
        customerSupport() {
            if (ngcom.customer.department == "" || ngcom.customer.subject == "" || ngcom.customer.message == "") {
                $('input[name=customer-subject]').css('border-color', 'red')
                $('select.form-control').css('border-color', 'red')
                $('textarea[name=customer-message]').css('border-color', 'red')
                alert("PLEASE COMPLETE ALL FIELDS")
            } else {
                $('input[name=customer-subject]').css('border-color', '#ced4da')
                $('select.form-control').css('border-color', '#ced4da')
                $('textarea[name=customer-message]').css('border-color', '#ced4da')

                $.ajax({
                    type: "post",
                    url: BASEURL + "contact/message",
                    data: ngcom.customer,
                    success: function (response) {
                        if (response === '1' || response === 1) {
                            alert("Message Sent Successfully!");
                            ngcom.customer.message = ""
                            ngcom.customer.subject = ""
                            ngcom.customer.department = "Please Select a Department"
                        } else {
                            alert("Message sending failed! Please try again")
                        }
                    }
                })
            }
        },
        updateProfile() {
            //console.log(ngcom.profile);

            $.ajax({
                type: 'post',
                data: ngcom.profile,
                url: BASEURL + "cardpayment/updateprofile",
                success: function (response) {
                    if (response === "Update Successful") {
                        alert("Profile successfully Updated");
                        window.location.reload();
                    } else {
                        alert("Error Updating Profile.... Please Try Again")
                    }
                }
            })
        },
        openCurrentField() {
            if ($('input[name="current-password"]').attr('type') == 'password') {
                $('input[name="current-password"]').attr('type', 'text')
                $('#basic-addon1').removeClass('fa-eye');
                $('#basic-addon1').addClass('fa-eye-slash');
            } else {
                $('input[name="current-password"]').attr('type', 'password');
                $('#basic-addon1').removeClass('fa-eye-slash');
                $('#basic-addon1').addClass('fa-eye');
            }
        },
        openNewField() {
            if ($('input[name="new-password"]').attr('type') == 'password') {
                $('input[name="new-password"]').attr('type', 'text')
                $('#basic-addon2').removeClass('fa-eye');
                $('#basic-addon2').addClass('fa-eye-slash');
            } else {
                $('input[name="new-password"]').attr('type', 'password');
                $('#basic-addon2').removeClass('fa-eye-slash');
                $('#basic-addon2').addClass('fa-eye');
            }
        },
        manuallyVerifyPayment() {
            setTimeout(function () {
                return window.location.reload();
            }, 3000);
            $.blockUI({
                message: '<h3>Please Wait...</h3>',
                css: {
                    backgroundColor: '#E5EFF1', color: 'black',
                    padding: "10px", borderRadius: "5px", border: "0"
                }
            });
            $.ajax({
                type: 'get',
                url: BASEURL.substring(BASEURL.indexOf('index.php'), -BASEURL.length) + "payment/verifypayment",
                success: function (response) {
                    //console.log(response, ' Response from verification.')
                }
            });
            // setTimeout(function () {
            // $('#historyModal').modal('show');
            // }, 3000)
            // this.fetchPaymentHistory();
        },
        openManualPayment() {

            $('#enterpaymentmanually').modal('show');
            this.fetchUsers();
        },
        viewReceipt(id) {
            //console.log(id)
            $.ajax({
                type: 'get',
                data: {id},
                url: BASEURL + "payments/fetchReceipt",
                success: function (response) {
                    //console.log(response);
                    if (response.status) {
                        $('.modal').modal('hide');
                        $('#userReceipt').modal('show');
                        ngcom.userreceipt = response.message
                    }
                }
            });
        }
    },
    computed: {
        filterPaymentList() {
            return ngcom.userlist.filter(function (user) {
                return user.username.toLowerCase().match(ngcom.searchusers.toLowerCase()) || user.firstname.toLowerCase().match(ngcom.searchusers.toLowerCase()) || user.lastname.toLowerCase().match(ngcom.searchusers.toLowerCase()) || user.email.toLowerCase().match(ngcom.searchusers.toLowerCase())
            })
        },
        sortUser() {
            if (ngcom.userlist.length > 0) {
                return   ngcom.userlist.sort(function (a, b) {
                    if (a.firstname < b.firstname) {
                        return -1;
                    }
                    if (a.firstname > b.firstname) {
                        return 1;
                    }
                    return 0;
                })
            } else {
                return []
            }
        }
    },
    created() {
        this.fetchCardInfo();
    }
});

