function _getSaveFunction(){
    try{
        return backend.save_model_to_file
    } catch (error) {
        console.error("Error saving file:", error)
        return (fileName)=>{
            console.log("Saving file as:", fileName)
            return true

        }
    }
}
function onSaveFileAs(model, fileName, dialect, onSuccess, onError) {
    const saveModelToFile = _getSaveFunction();
    if(!saveModelToFile(fileName, dialect, model)){
        if(onError){
            onError()
        }
    }
    if(onSuccess){
        onSuccess()
    }
}
function determineDialect(fileName){
    return backend.get_dialect(fileName)
}
function onOpenFile(filename, dialect, model){
    console.log("Opening file: " + filename)
    const success = backend.load_model_from_file(filename, dialect, model)
    if(success){
        console.log("Opened file: " + filename)
    }
    return success
}