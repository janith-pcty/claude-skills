using Paylocity.Distribution.PrintPlatform.Domain.PrintJob;
using System.Diagnostics.CodeAnalysis;

namespace Paylocity.Distribution.PrintPlatform.WebApi.Infrastructure.AddressApi;

[ExcludeFromCodeCoverage]
public class StubAddressHttpClient : IAddressHttpClient
{
  public Task<Address> GetDeliveryAddress(
    Guid deliveryAddressId,
    CancellationToken cancellationToken)
  {
    return Task.FromResult(Address.Create(
      deliveryAddressId,
      "123 Local Test St",
      "",
      "Schaumburg",
      "IL",
      "60173",
      "Cook",
      "US"));
  }
}
