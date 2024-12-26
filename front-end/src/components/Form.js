import React, { useState } from "react"

export default function Form({handleUserDataSubmit}){
    const [userData, setUserData] = useState({
        url:"",
        curriculum:""
    })

    const handleChange = (event) => {
        const {name, value, files} = event.target

        if(name === "curriculum")
            setUserData(prevUserData => {
                return {...prevUserData, [name]:files[0]}
            })
        else
            setUserData(prevUserData => {
                return {...prevUserData, [name]:value}
            })    
    }

    return (
        <form onSubmit={handleUserDataSubmit}>
            <label>
                URL: 
                <input 
                type="url"
                name="url"
                value={userData.url}
                onChange={handleChange}
                placeholder="Digite uma URL"
                />
            </label>

            <br />

            <label>
                Arquivo PDF:
                <input
                type="file"
                name="curriculum"
                accept=".pdf" // Permite apenas arquivos PDF
                onChange={handleChange}
                />
            </label>

            <br />

            <button type="submit">Enviar</button>

        </form>

    )
}