var video_hash = video_info['video_hash']
var video_name = video_info['video_name']
var link = 'https://www.youtube.com/watch?v=' + video_info['video_hash']

var tag = document.createElement('script');

tag.src = "https://www.youtube.com/iframe_api";
var firstScriptTag = document.getElementsByTagName('script')[0];
firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);

var player;
var previous_frame = -1

if(group==1){
    var height = 360;
    var width = 640;
}else{
    var height = 540;
    var width = 960;
}

function onYouTubeIframeAPIReady() {
    player = new YT.Player('player', {
        height: height,
        width: width,
        videoId: video_hash,
        events: {
        'onReady': onPlayerReady,
        'onStateChange': onPlayerStateChange
        }
    });
}
// 4. The API will call this function when the video player is ready.
function onPlayerReady(event) {
    // setFileContent()
    setInterval(monitor_player, 500)
    // event.target.playVideo();
}

// 5. The API calls this function when the player's state changes.
//    The function indicates that when playing a video (state=1),
//    the player should play for six seconds and then stop.
var done = false;
function onPlayerStateChange(event) {
    if (event.data == YT.PlayerState.PLAYING && !done) {
        // setTimeout(stopVideo, 6000);
        done = true;
    }
    setFileContent(false)
}

function stopVideo() {
    player.stopVideo();
}

if(group==1 && video_info.ocr != undefined){
    var editors = {}
    for(var cluster in video_info['ocr']['file_names']){
        editors[cluster] = CodeMirror.fromTextArea(document.getElementById("file-"+cluster+"-text"), {
            lineNumbers: true,
            matchBrackets: true,
            readOnly: true,
            mode: "text/x-java"
        });
        editors[cluster].setSize("100%", "400px")
    }

    $( "#navigation" ).tabs({
        beforeActivate: function (event, ui) {
            setFileContent(true)
        }
    });

    $( "#files-2" ).tabs({
        beforeActivate: function (event, ui) {
            cid = ui.newPanel.attr('cluster')
            setTimeout(function() {editors[cid].refresh();}, 0.5);
        }
    }).addClass( "ui-tabs-vertical ui-helper-clearfix" );
    $( "#files-2 li" ).removeClass( "ui-corner-top" ).addClass( "ui-corner-left" );

}


function setFileContent(refresh){
    if(video_info.ocr == undefined){
        return
    }

    t = parseInt(player.getCurrentTime())
    ocr = video_info['ocr']
    
    for(i=ocr['frames'].length; i>=0; i--){
        frame = ocr['frames'][i]
        if(t >= frame){
            break
        }
    }
    
    if(frame == previous_frame && !refresh){
        return
    }
    previous_frame = frame

    docs = video_info['ocr']['docs']
    file_id = docs[frame+""]['cluster']
    file_lines = docs[frame+""]['lines']
    $("#files-2").tabs("option", "active", file_id);  
    editors[file_id].setValue(file_lines)
    
    console.log(t+"/"+frame + "/" + file_id)
    // editors[file_id].refresh();
    setTimeout(function() {
        editors[file_id].refresh();
    },1);
    // $("#tabs-file-"+file_id).html(file_lines.join("<br/>"))
}

function monitor_player(){
    if(video_info.ocr == undefined || player == undefined){
        return
    }
    
    setFileContent()
}

$('.action').each(function(idx){
    $(this).on("click", function(){
        this.classList.toggle("active");
        var content = this.nextElementSibling;
        if(content != null){
            if (content.style.display === "block") {
                content.style.display = "none";
            } else {
                content.style.display = "block";
            }
        }
    });
})

$('.timestamp').each(function(idx){
    $(this).on("click", function(){
        frame2 = parseInt($(this).attr("frame2"))
        player.seekTo(frame2-5)
        // setTimeout(player.pauseVideo(), 1000);
    })
})

$("button[name='btnAnalyze']").click(function(){
    console.log('process ' + link)
    $('#progress').html("")

    pullvideo(link)
})

$("button[name='btnViewPredict']").click(function(){
    window.open("/video/predict?v="+video_info['video_hash'], "_blank")
})

$("button[name='btnViewCrop']").click(function(){
    window.open("/video/crop?v="+video_info['video_hash'], "_blank")
})

$("button[name='btnViewOCR']").click(function(){
    window.open("/video/ocr?v="+video_info['video_hash'], "_blank")
})

function pullvideo(youtube_url){
    $.ajax({
        url: '/pullvideo',
        type: 'post',
        contentType: "application/json", 
        data: JSON.stringify({'url': youtube_url}),
        beforeSend: function(){
            $('#progress').append('<p>start to download video from youtube...</p>')
        },
        success: function(data){
            video_hash = data['video_hash']
            video_name = data['video_name']

            $('#progress').append('<p>finish to download video [' + video_name + ']</p>')
            
            diffvideo(video_hash, video_name)
        }
    })
}

function diffvideo(video_hash, video_name){
    $.ajax({
        url: '/diffvideo',
        type: 'post',
        contentType: "application/json", 
        data: JSON.stringify({'video_hash': video_hash, 'video_name': video_name}),
        beforeSend: function(){
            $('#progress').append('<p>start to extract distinct frames from video...</p>')
        },
        success: function(data){
            $('#progress').append('<p>finish to extract distinct frames from video</p>')
            predictvideo(video_hash, video_name)
        }
    })
}

function predictvideo(video_hash, video_name){
    $.ajax({
        url: '/predictvideo',
        type: 'post',
        contentType: "application/json", 
        data: JSON.stringify({'video_hash': video_hash, 'video_name': video_name}),
        beforeSend: function(){
            $('#progress').append('<p>predicting frames in video...</p>')
        },
        success: function(data){
            $('#progress').append('<p>finish to predict frames in video</p>')
            cropvideo(video_hash, video_name)
        }
    })
}

function cropvideo(video_hash, video_name){
    $.ajax({
        url: '/cropvideo',
        type: 'post',
        contentType: "application/json", 
        data: JSON.stringify({'video_hash': video_hash, 'video_name': video_name}),
        beforeSend: function(){
            $('#progress').append('<p>start to detect code area in frames...</p>')
        },
        success: function(data){
            $('#progress').append('<p>finish to detect code area in frames</p>')
        }
    })
}



function frameFormat(frame){
	var hour = parseInt(frame / 3600);
	var minute = parseInt((frame - hour*3600) / 60);
	var second = parseInt(frame - hour*3600 - minute*60);
	
	if(hour > 0){
		return formatNumberLength(hour,2) + ":" + formatNumberLength(minute,2) + ":" + formatNumberLength(second,2);
	}
	else{
		return formatNumberLength(minute,2) + ":" + formatNumberLength(second,2);
	}
}


function formatNumberLength(num, length) {
    var r = "" + num;
    while (r.length < length) {
        r = "0" + r;
    }
    return r;
}


function search(q)
{   
    var frames = []
    var docs = video_info['ocr']['docs'];
    for(var frame in docs){
        file_lines = docs[frame+""]['lines'];

        if(file_lines.toLowerCase().indexOf(q.toLowerCase()) >= 0){
            frames.push(frame);
        }
    }

	if(frames.length <= 0) return;
			
    $('#search_result').html('');
    for(i=0; i<frames.length; i++){
        if((i) % 10 == 0)
        {	
            var tr = $('<div></div>')
            $('#search_result').append(tr);
        }
        
        tr.append('<span class="time_span" frame="' + frames[i] + '">' + frameFormat(frames[i])+"</span>");
    }
    
    $('#search').css('display', 'block');
    $('#search').popup('show');
    
    var pos = $('[name=query]').position();
    $("#search").css({top: pos.top, left: pos.left + 450, position:'absolute'});
    $('#search_result').css('width', '100%');
    $('#search_result').css('height', '100%');
    
    $('.time_span').click(function(){
        var t = $(this).attr('frame');
        console.log('goto ' + t);
        player.seekTo(t);
        // stopVideo();
    });
}