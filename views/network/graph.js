
		var editmode = false;
        var newitems = false;

	$(".pushme").click(function () {
    var $element = $(this);
    $element.val(function(i, text) {
        editmode = !editmode;
        console.log (editmode);
        return text == $element.data('default-text') ? $element.data('new-text')
                                                     : $element.data('default-text');
    });
	});

        /*var d3nodes  = [{"id":2,"title":"can I edit","x":230,"y":494},{"id":3,"title":"test","x":436,"y":309}]*/
        var d3nodes = {{=XML(d3nodes)}};
        var vieweventmap = false;
        var eventowner = false;
        var height = 350 + (d3nodes.length * 25);
        var redraw = true;

        /*var d3edges = [];
        var d3edges = [{"source":2,"target":3}]
        var d3edges = [{"source":13,"target":14}]*/
        var d3edges = {{=XML(d3edges)}};

        d3edges.forEach(function(e, i){
              d3edges[i] = {source: d3nodes.filter(function(n){return n.serverid == e.source;})[0],
                          target: d3nodes.filter(function(n){return n.serverid == e.target;})[0],
                          dasharray: e.dasharray,
                          sourceid: e.source}});


        function requestLink(sourceId,targetId)
        {
        ajax('{{=URL('network','linkrequest')}}'+'/'+sourceId+'/'+targetId+'/', ['bla'], 'ajaxlink');
        };

        function deleteLink(sourceId,targetId)
        {
        ajax('{{=URL('network','linkrequest')}}'+'/'+sourceId+'/'+targetId+'/delete/', ['bla'], 'ajaxlink');
        };

        function moveElement(sourceId, sourceposx, sourceposy)
        {
        ajax('{{=URL('event','move')}}'+'/'+0+'/'+sourceId+'/'+sourceposx+'/'+sourceposy+'/', ['bla'], 'ajaxlink');
        };

        var ajaxquesturl = '{{=URL('network','ajaxquest')}}?'

        function out(m) {
        $('#message').html(m);
        };