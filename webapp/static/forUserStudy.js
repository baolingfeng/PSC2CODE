var video_hash = video_info['video_hash']
var video_name = video_info['video_name']

var previous_frame = -1

if(group==1){
    $('#player').width(640);
    $('#player').height(360);
}else{
    $('#player').width(1280);
    $('#player').height(720);
}


var v = document.getElementById('player');
v.addEventListener('timeupdate', function(){
    if(video_info.ocr == undefined || player == undefined){
        return
    }
    
    setFileContent()
});


if(group ==1 && video_info.ocr != undefined){
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

    t = v.currentTime
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
    setTimeout(function() {
        editors[file_id].refresh();
    },1);
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
        v.currentTime = frame2 - 5;
    })
})

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
        v.currentTime = t;
        v.pause();
    });
}
