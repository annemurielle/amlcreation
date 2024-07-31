<%@ Page Language="C#" AutoEventWireup="true" CodeBehind="ContactForm.aspx.cs" validateRequest="false" Inherits="ContactForm.ContactForm" %>

<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">

<html xmlns="http://www.w3.org/1999/xhtml" >
<head runat="server">
    <title>Votre message</title>
    	<link rel="stylesheet" type="text/css" media="screen,projection" href="StyleSheet.css"/>
	
    

</head>
<body  scroll="auto">
    <form id="form1" runat="server">
    <div>
    
    <asp:Panel ID="formPanel" Visible="true" runat="server">
    <p />

    <div >
        <h2><asp:Label ID="contactLabel" runat="server"></asp:Label></h2>
    </div>
    
    <p />
    <table cellpadding="0" cellspacing="0">
    <tr><td><h1>Votre Message</h1></td></tr>
    <tr>
        <td >
            <fieldset style="width:450px;">
            <legend>Information</legend>
                   <asp:ValidationSummary ID="valSum" runat="server" />
                   <p>
                  <label for="nameBox">Nom/Pseudo*</label>&nbsp;<asp:TextBox Width="70%" ID="nameBox" runat="server" MaxLength="50"/>
                <asp:RequiredFieldValidator ID="nameReqVal"  ErrorMessage="Veuillez saisir un nom/pseudo"  
                ControlToValidate="nameBox" runat="server" /> 
                
               </p>
<p>
                 <label for="urlWebSiteBox">Site</label>&nbsp;<asp:TextBox  Width="70%"                  
                 ID="urlWebSiteBox" runat="server" MaxLength="100" />                 <asp:RegularExpressionValidator ID="urlRegVal" 
                            ValidationExpression="^http\://[a-zA-Z0-9\-\.]+\.[a-zA-Z]{2,3}(/\S*)?$" 
                                ControlToValidate="urlWebSiteBox" 
                                    ErrorMessage="Veuillez saisir un site correct" 
                                        runat="server"></asp:RegularExpressionValidator>
             </p>
             <p>
                 <label for="emailBox">Email</label>&nbsp;<asp:TextBox Width="70%"  ID="emailBox" runat="server" MaxLength="100"/>
                        <asp:RegularExpressionValidator ID="emailRegVal" 
                            ValidationExpression="\w+([-+.]\w+)*@\w+([-.]\w+)*\.\w+([-.]\w+)*" 
                                ControlToValidate="emailBox" 
                                    ErrorMessage="Veuillez saisir un email correct" 
                                        runat="server"></asp:RegularExpressionValidator></p>
                   
            </fieldset>  
        </td>
    </tr>    
    <tr>
        <td  align="right">
        <br />
            <fieldset style="width:450px;">
            <legend id="legendMessage" runat="server">Message*</legend>
            
                  <asp:textbox ID="messageBox" Width="70%" TextMode="MultiLine" 
                        Rows="8" runat="server"></asp:textbox>
                    <asp:RequiredFieldValidator ID="messageReqVal" ControlToValidate="messageBox" 
                        ErrorMessage="Veuillez saisir un message" runat="server">*</asp:RequiredFieldValidator> 
                              
            </fieldset>
        </td>
    </tr>
    <tr><td><br /></td></tr>
    <tr>
        <td align="right" >
            <asp:Button ID="submitBtn" Text="Envoyer" Width="80" runat="server" OnClick="SubmitBtn_Click" />
            <asp:Button ID="resetBtn" Text="Annuler" Width="60" CausesValidation="false" 
                OnClick="ResetBtn_Click" runat="server" />
        </td>
    </tr>
    </table>
    <br />
</asp:Panel>

<asp:Panel ID="successPanel" Visible="false" runat="server">
    <br /><br />
    <table align="center" width="400" cellpadding="0" cellspacing="0">
    <tr>
        <th align="center">
            <b>Message envoyé</b>
        </th>
    </tr>
    <tr>
        <td>
            <p />
            Merci beaucoup pour votre message. Il sera publié dès que le responsable du site en aura pris connaissance et l'aura validé. 
            <p />            
        </td>
    </tr>
    </table>
</asp:Panel>

<asp:Panel ID="errorPanel" Visible="false" runat="server">  
    <br /><br />
    <table align="center" width="400" cellpadding="0" cellspacing="0">
    <tr>
        <th align="center">
            <b>Problème...</b>
        </th>
    </tr>
    <tr>
        <td>
            <p />
           Une erreur s'est produite, vous pouvez réessayer plus tard.
        </td>
    </tr>
    </table>
    </asp:Panel>
    
    </div>
    </form>
</body>
</html>
