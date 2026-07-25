describe('VeraRecording_manualcrawl Recorded Session', () => {
  it('plays back successfully', () => {
    cy.visit('/');
    cy.xpath('id("HyperLink1")/IMG[1]').click();
    cy.get('#AccountLink').click();
    cy.get('[name="uid"]').type('test');
    cy.get('[name="passw"]').type('test');
    cy.get('[name="btnSubmit"]').click();
    cy.xpath('id("MenuHyperLink6")').click();
  });
});