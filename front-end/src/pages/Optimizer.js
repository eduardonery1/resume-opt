import React from "react"
import OptimizerView from "./OptimizerView"
import { handleUserDataSubmit } from "../models/resumeAPI"

export default function Optimizer(){

    return (
        <OptimizerView {...{handleUserDataSubmit,}}/>
    )
}