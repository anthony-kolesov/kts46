function SimpleComponent(){}

SimpleComponent.prototype = {

    get yourName()        { return this.mName; },
    set yourName(aName)   { return this.mName = aName; },

    write: function () { dump("Hello " + this.mName + "\n"); },
    change: function (aValue) { this.mName = aValue; },
    mName: "a default value",

    QueryInterface: function (iid) {
        if (!iid.equals(Components.interfaces.nsISimple)
            && !iid.equals(Components.interfaces.nsISupports))
        {
            throw Components.results.NS_ERROR_NO_INTERFACE;
        }
        return this;
    }
}

var Module = {
    firstTime: true,

    registerSelf: function (compMgr, fileSpec, location, type) {
        if (this.firstTime) {
            dump("*** Deferring registration of simple JS components\n");
            this.firstTime = false;
            throw Components.results.NS_ERROR_FACTORY_REGISTER_AGAIN;
        }
        debug("*** Registering sample JS components\n");
        compMgr =
compMgr.QueryInterface(Components.interfaces.nsIComponentRegistrar);
        compMgr.registerFactoryLocation(this.myCID,
                                        "Simple JS Component",
                                        this.myProgID,
                                        fileSpec,
                                        location,
                                        type);
    },

    getClassObject : function (compMgr, cid, iid) {
        if (!cid.equals(this.myCID))
        throw Components.results.NS_ERROR_NO_INTERFACE
        if (!iid.equals(Components.interfaces.nsIFactory))
        throw Components.results.NS_ERROR_NOT_IMPLEMENTED;
        return this.myFactory;
    },

    myCID: Components.ID("{98aa9afd-8b08-415b-91ed-01916a130d16}"),
    myProgID: "@mozilla.org/js_simple_component;1",

    myFactory: {
        createInstance: function (outer, iid) {
            dump("CI: " + iid + "\n");
            if (outer != null)
            throw Components.results.NS_ERROR_NO_AGGREGATION;
            return (new SimpleComponent()).QueryInterface(iid);
        }
    },

    canUnload: function(compMgr) {
        dump("****** Unloading: Simple JS component! ****** \n");
        return true;
    }
}; // END Module

function NSGetModule(compMgr, fileSpec) { return Module; }