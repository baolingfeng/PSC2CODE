var starttime = "";
var intervalId = null;

submit_button_val1 = ' Start to Watching Video & Answer Questions ';
submit_button_val2 = ' Submit '
	

function initQuestionnaire()
{
	$.ajax({
		type: 'post',
		contentType: "application/json",
		url: '/VTRevolution/QuestionnaireSession?type=get&video='+videoName,
		success: function(d){
			console.log(d);
			
			var starttime = new Date();
			if(d != "")
			{	
				$(".qdiv").each(function(){
					$(this).removeClass("disable-text");
					$(this).addClass("w3-light-grey");
				});
				
				for(i=1; i<=questionNumber; i++)
				{
					$("input[name=q"+i+"]").prop('disabled', false);
				}
				
				$("input[name=starttime]").val(d);
				starttime = createDateAsUTC(new Date(d));
				
				intervalId = setInterval(function () {
					//console.log(new Date() + " - " + starttime);
					var second = (createDateAsUTC(new Date()) - starttime) / 1000;
					$("#timecounter").html(second);
				}, 1000);
				
				$("#timecounter_span").css("display", "");
	
				$("input[name=controlBtn]").val(submit_button_val2)
			}
			else
			{
				resetQuestionPage(questionNumber);
			}
		}
	});
}

function beginAnswer(n, videoName, group)
{
	$(".qdiv").each(function(){
		$(this).removeClass("disable-text");
		$(this).addClass("w3-light-grey");
	});
	
	for(i=1; i<=n; i++)
	{
		$("input[name=q"+i+"]").prop('disabled', false);
	}
	
	starttime = createDateAsUTC(new Date());
	$("#timecounter_span").css("display", "");
	$("#timecounter").html(0);
	
	$("input[name=starttime]").val(starttime.toISOString().slice(0, 19));
	
	intervalId = setInterval(function () {
		var second = (createDateAsUTC(new Date()) - starttime) / 1000;
		$("#timecounter").html(second);
	}, 1000);
	
	$("input[name=controlBtn]").val(submit_button_val2);
	 
    if(group==1){
        window.open("enhanced?v="+videoName+"&group="+group+"&youtube="+use_youtube, "_blank");
    }
    else{
        window.open('https://www.youtube.com/watch?v='+videoName, "_blank");
    }
}

function submitQuestionnaire(n, videoName, group)
{
	var r = confirm("Are you sure to submit the questionnario");
	if (!r)  return;
	
	console.log("submit...");
	answers = {};
	
	answers['starttime'] = $("input[name=starttime]").val();
	answers['endtime'] = createDateAsUTC(new Date()).toISOString().slice(0, 19);
	
	answers['qnumber'] = n;
	answers['email'] = $("input[name=useremail]").val();
	answers['group'] = $("input[name=group]").val();
	answers['video'] = videoName;
	
	var canSubmit = true;
	for(i=1; i<=n; i++)
	{
		var types = new Set();
		$("input[name=q"+i+"]").each(function(){
			types.add($(this).prop('type'))
		});
		
		types = Array.from(types);
		if(types.length == 1)
		{
			var type = types[0];
			if(type == "checkbox" || type == "radio")
			{
				var checkedValues = [];
				$('input[name="q'+ i + '"]:checked').each(function() {
					checkedValues.push(this.value);
				});
				
				if(checkedValues.length > 0)
				{
					answers["q"+i] = checkedValues.join(",");
					answers["q"+i+"_time"] = $("input[name=q"+i+"_time]").val();
					$("span[name=q"+i+"_warning]").addClass("hidden-text");
				}
				else
				{
					canSubmit = false;
					$("span[name=q"+i+"_warning]").removeClass("hidden-text");
				}
			}
			else if(type == "text" || type == "textarea")
			{
				var inputValues = [];
				var allNonEmpty = true;
				$("input[name=q"+i+"]").each(function() {
					if(this.value.trim() != "")
					{
						inputValues.push(this.value);
					}
					else
					{
						allNonEmpty = false;
					}
				});
				
				if(inputValues.length > 0)
				{
					answers["q"+i] = inputValues.join(",");
					answers["q"+i+"_time"] = $("input[name=q"+i+"_time]").val();
					$("span[name=q"+i+"_warning]").addClass("hidden-text");
				}
			}
		}
		else
		{
			
		}
		
	}
	console.log(answers);
	
	if(canSubmit)
	{
		$(".overall-warning").addClass("hidden-text");
		$.ajax({
			type: 'post',
            url: 'survey/submit',
            contentType: "application/json",
			data: JSON.stringify(answers),
			beforeSend: function() {
		       console.log("submitting...")
		    },
			success: function(d){
				record_id = d['record_id']
				
				var r = confirm("submit success!");
				// resetAnswer(n, videoName, group);

				window.location = "survey/done?id="+record_id+"&group="+group;
			},
			error: function(xhr, status, error) {
				var err = eval("(" + xhr.responseText + ")");
				alert(err.Message);
			}
		});
	}
	else
	{
		$(".overall-warning").removeClass("hidden-text");
		$("html, body").animate({ scrollTop: 0 }, "slow");
	}
}

function startAnswer(n, button, videoName, group)
{
	console.log(button);
	
	if(button == submit_button_val1)
	{
		beginAnswer(n, videoName, group);
	}
	else if(button == submit_button_val2)
	{
		submitQuestionnaire(n, videoName, group);
	}
	
}

function submitRate(recordId, group)
{
	var canSubmit = true;
	var rates = []
	for(i=1; i<=10; i++)
	{   
        if($("input[name=r" + i + "]").length == 0){
            break
        }

		var res = $("input[name=r" + i + "]:checked");
		console.log(res);
		if(res.length <= 0)
		{
			canSubmit = false;
			rates.push(-1);
		}
		else
		{
			rates.push(res.val());
		}
	}
	var comment = $("textarea[name='comment']").val();
	
	if(canSubmit)
	{
		$.ajax({
            type: 'post',
            contentType: "application/json",
			data: JSON.stringify({'record_id': recordId, 'rate': rates.join(','), 'comment': comment}),
			url: '/survey/rate',
			beforeSend: function() {
		       console.log("submitting rate.....")
		    },
			success: function(d){
				console.log(d);
				
				var r = confirm("Thank you for your participation!");
                
                // setTimeout("self.close()", 1)
				window.location = "/?group="+group;
			},
			error: function(xhr, status, error) {
				var err = eval("(" + xhr.responseText + ")");
				alert(err.Message);
			}
		});
	}
	else
	{
		$(".warning-text").removeClass("hidden-text");
	}
	
}

function closeWindow()
{
	var browserName = navigator.appName;
    var browserVer = parseInt(navigator.appVersion);
    
    if(browserName == "Microsoft Internet Explorer"){
        var ie7 = (document.all && !window.opera && window.XMLHttpRequest) ? true : false;  
        if (ie7)
        {  
          window.open('','_parent','');
          window.close();
        }
       else
        {
          this.focus();
          self.opener = this;
          self.close();
        }
    }
    else{  
       try{
           this.focus();
           self.opener = this;
           self.close();
       }catch(e){}

       try{
    	   netscape.security.PrivilegeManager.enablePrivilege("UniversalBrowserWrite");
    	   window.open('','_self');
    	   window.close();
       }catch(e){ }
   }
}

function resetQuestionPage(n)
{
	$(".qdiv").each(function(){
		$(this).addClass("disable-text");
		$(this).removeClass("w3-light-grey");
	});
	
	for(i=1; i<=n; i++)
	{
		$("input[name=q"+i+"]").prop('disabled', true);
		
		var type = $("input[name=q"+i+"]").prop('type');
		if(type == "checkbox" || type == "radio")
		{
			$("input[name=q"+i+"]").prop('checked', false);
		}
		else if(type == "text" || type == "textarea")
		{
			$("input[name=q"+i+"]").val('');
		}
		
		$("input[name=q"+i+"_time]").val('');
		
		$("span[name=q"+i+"_warning]").addClass("hidden-text");
	}
	
	$("input[name=controlBtn]").val(submit_button_val1)
	$("#timecounter_span").css("display", "none");
	$(".overall-warning").addClass("hidden-text");
	
	clearInterval(intervalId);
}

function resetAnswer(n, videoName, group)
{
	$.ajax({
		type: 'post',
		contentType: "application/json",
		url: '/VTRevolution/QuestionnaireSession?type=reset&video='+videoName,
		success: function(d){
			console.log(d);
			
			resetQuestionPage(n);
		}
	});
	
}

function backToTop()
{
	$("html, body").animate({ scrollTop: 0 }, "slow");
}

function createDateAsUTC(date) {
    return new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate(), date.getHours(), date.getMinutes(), date.getSeconds()));
}

function convertDateToUTC(date) { 
    return new Date(date.getUTCFullYear(), date.getUTCMonth(), date.getUTCDate(), date.getUTCHours(), date.getUTCMinutes(), date.getUTCSeconds()); 
}