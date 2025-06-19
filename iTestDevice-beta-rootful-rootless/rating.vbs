Dim fso, file, folderPath
Dim rating, dt, pcName, logLine

Dim answer
answer = MsgBox("Would you like to rate us?", vbYesNo + vbQuestion, "iTester")

If answer = vbYes Then
    Do
        rating = InputBox("You can rate the tool from 1 to 5 stars. Please enter your rating:", "Tool Rating")
        If rating = "" Then
            MsgBox "Rating cancelled.", vbInformation, "Cancelled"
            WScript.Quit
        ElseIf Not IsNumeric(rating) Or CInt(rating) < 1 Or CInt(rating) > 5 Then
            MsgBox "Please enter a valid number between 1 and 5.", vbExclamation, "Invalid Input"
        Else
            Exit Do
        End If
    Loop

    ' Tarih ve saat formatı
    dt = Year(Now) & "-" & Right("0" & Month(Now), 2) & "-" & Right("0" & Day(Now), 2) & " " & _
         Right("0" & Hour(Now), 2) & ":" & Right("0" & Minute(Now), 2)

    ' Bilgisayar adı al
    Set wshNetwork = CreateObject("WScript.Network")
    pcName = wshNetwork.ComputerName

    ' Log satırı hazırla
    logLine = dt & " - " & pcName & " - Rating: " & CInt(rating)

    ' Dosya yolu
    Set fso = CreateObject("Scripting.FileSystemObject")
    folderPath = fso.GetParentFolderName(WScript.ScriptFullName)

    ' Dosyayı oluşturup yaz (üzerine yazacak)
    Set file = fso.CreateTextFile(folderPath & "\rating.log", True)
    file.WriteLine logLine
    file.Close

    MsgBox "Thank you for rating the tool!" & vbCrLf & vbCrLf & "Your rating: " & CInt(rating), vbInformation, "Rating Received"
Else
    MsgBox "No problem! Thank you.", vbInformation, "iTester"
End If
