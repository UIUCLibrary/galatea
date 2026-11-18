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

const ERROR_LEVEL = 40
const WARNING_LEVEL = 30
const INFO_LEVEL = 20
const DEBUG_LEVEL = 10

/**
 * Get the correct console reporter based on the log level provided.
 *
 * @param level - log level that the message should be reported as.
 * @param maxReportingLevel - highest log level that should be reported. Anything less will be a no-op
 * @returns {(function(*): void)|(function())|*|((...data: any[]) => void)|(function(*): void)} - Callable function to for reporting data
 */
function getConsoleLoggingFunction(level, maxReportingLevel){
    if (maxReportingLevel <= ERROR_LEVEL && level >= ERROR_LEVEL){
        return (message) => {
            return console.error("ERROR: " + message)
        }
    }

    // WARNING
    if (maxReportingLevel <= WARNING_LEVEL && level >= WARNING_LEVEL){
        return (message) => {
            return console.warn("WARNING: " + message)
        }
    }

    // INFO
    if (maxReportingLevel <= INFO_LEVEL && level >= INFO_LEVEL){
        return console.log
    }

    // DEBUG
    if (maxReportingLevel <= DEBUG_LEVEL && level >= DEBUG_LEVEL){
        return (message) => {
            console.debug("DEBUG: ", message)
        }
    }
    return ()=>{}
}

function logAction(message, level, reportingLevel=INFO_LEVEL){
    const logFunc = getConsoleLoggingFunction(level, reportingLevel)
    logFunc( message)
}